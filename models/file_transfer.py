import os
import uuid
import base64
import time
import mimetypes
import math
from utils.printer import verbose_log
from utils.time_utils import current_unix_time
from utils.token_utils import generate_token
from core.ack_registry import register_ack
from datetime import datetime

def format_verbose(direction, ip, msg_type, message_dict):
    """
    RFC-compliant verbose format:
    SEND >/RECV <  [timestamp] (ip) TYPE=...
    key: value...
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"{direction} [{timestamp}] ({ip}) TYPE={msg_type}"
    body = "\n".join(f"{k}: {v}" for k, v in message_dict.items())
    return f"{header}\n{body}\n"

class FileTransfer:
    def __init__(self, from_profile, to_profile, file_location, description, listener, filename=""):
        self.from_profile = from_profile
        self.to_profile = to_profile
        self.file_location = file_location
        self.description = description
        self.filename = filename
        self.listener = listener
        self.file_id = uuid.uuid4().hex
        self.chunk_size = 1024

    def file_offer(self):
        file_size = os.path.getsize(self.file_location)
        filename = os.path.basename(self.file_location)
        filename = self.filename if self.filename else filename
        filetype, _ = mimetypes.guess_type(self.file_location)
        filetype = filetype or "application/octet-stream"

        offer = {
            "TYPE": "FILE_OFFER",
            "FROM": self.from_profile.user_id,
            "TO": self.to_profile.user_id,
            "FILENAME": filename,
            "FILESIZE": str(file_size),
            "FILETYPE": filetype,
            "FILEID": self.file_id,
            "DESCRIPTION": self.description,
            "TIMESTAMP": str(int(time.time())),
            "TOKEN": generate_token(self.from_profile.user_id, 600, "file")
        }

        msg = "\n".join(f"{k}: {v}" for k, v in offer.items()) + "\n\n"
        self.listener.send_unicast(msg, self.to_profile.ip)

        # RFC Verbose log for outgoing
        verbose_log("SEND >", format_verbose("SEND >", self.to_profile.ip, offer["TYPE"], offer))

        register_ack(self.file_id, self.file_transmit)

    def file_transmit(self):
        file_size = os.path.getsize(self.file_location)
        total_chunks = math.ceil(file_size / self.chunk_size)
        
        with open(self.file_location, "rb") as f:
            for chunk_index in range(total_chunks):
                chunk = f.read(self.chunk_size)
                encoded_data = base64.b64encode(chunk).decode("utf-8")

                chunk_msg = {
                    "TYPE": "FILE_CHUNK",
                    "FROM": self.from_profile.user_id,
                    "TO": self.to_profile.user_id,
                    "FILEID": self.file_id,
                    "CHUNK_INDEX": str(chunk_index),
                    "TOTAL_CHUNKS": str(total_chunks),
                    "CHUNK_SIZE": str(len(chunk)),
                    "TOKEN": generate_token(self.from_profile.user_id, 600, "file"),
                    "DATA": encoded_data
                }

                msg = "\n".join(f"{k}: {v}" for k, v in chunk_msg.items()) + "\n\n"
                self.listener.send_unicast(msg, self.to_profile.ip)

                # RFC Verbose log for outgoing
                verbose_log("SEND >", format_verbose("SEND >", self.to_profile.ip, chunk_msg["TYPE"], chunk_msg))

                time.sleep(0.05)


class FileTransferResponder:
    def __init__(self, listener):
        self.listener = listener

    def send_ack(self, to_ip, message_id, status):
        ack = {
            "TYPE": "ACK",
            "MESSAGE_ID": message_id,
            "STATUS": status,
        }
        msg = "\n".join(f"{k}: {v}" for k, v in ack.items()) + "\n\n"
        self.listener.send_unicast(msg, to_ip)

        verbose_log("SEND >", format_verbose("SEND >", to_ip, ack["TYPE"], ack))

    def confirm_file_received(self, to_ip, from_user, to_user, file_id):
        confirm = {
            "TYPE": "FILE_RECEIVED",
            "FROM": from_user,
            "TO": to_user,
            "FILEID": file_id,
            "STATUS": "COMPLETE",
            "TIMESTAMP": str(int(time.time()))
        }
        msg = "\n".join(f"{k}: {v}" for k, v in confirm.items()) + "\n\n"
        self.listener.send_unicast(msg, to_ip)

        verbose_log("SEND >", format_verbose("SEND >", to_ip, confirm["TYPE"], confirm))

    def accept_file_offer(self, to_ip, file_id):
        self.send_ack(to_ip=to_ip, message_id=file_id, status="ACCEPTED")
