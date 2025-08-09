import os
import base64
from utils.token_utils import generate_token
from models.file_transfer import FileTransferResponder
from ui.cli import pending_file_offers  # import the shared queue

file_buffer = {}

def handle_file(msg: dict, addr: tuple, listener):
    """
    Handles file-related messages.
    This function is non-blocking — file offers are pushed to the CLI queue.
    """
    msg_type = msg["TYPE"]
    file_id = msg.get("FILEID")
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    ip = addr[0]


    if msg_type == "FILE_OFFER":
        # Just enqueue the offer for the CLI to handle later
        pending_file_offers.put((msg, addr))

        # Prepare file buffer entry in advance (optional)
        file_buffer[file_id] = {
            "filename": "received_" + msg["FILENAME"],
            "chunks": {},
            "total_chunks": int(msg.get("TOTAL_CHUNKS", 0)),
            "from_user": from_user,
            "to_user": to_user,
            "sender_ip": ip,
            "original_message_id": msg["MESSAGE_ID"]
        }

    elif msg_type == "FILE_CHUNK":
        if file_id not in file_buffer:
            print("⚠️ Received chunk for unknown file")
            return

        chunk_num = int(msg["CHUNK_INDEX"])
        data = base64.b64decode(msg["DATA"])
        file_buffer[file_id]["chunks"][chunk_num] = data

        if len(file_buffer[file_id]["chunks"]) == file_buffer[file_id]["total_chunks"]:
            save_chunks(file_id, file_buffer[file_id], listener)

    elif msg_type == "FILE_RECEIVED":
        print(f"✅ Peer confirmed file {msg.get('FILEID')} was saved (STATUS: {msg.get('STATUS')}).")

    elif msg_type == "ACK":
        print(f"📨 ACK from {from_user}: {msg['STATUS']} for {msg['MESSAGE_ID']}")

def save_chunks(file_id, buffer, listener):
    filename = buffer["filename"]
    with open(filename, "wb") as f:
        for i in sorted(buffer["chunks"]):
            f.write(buffer["chunks"][i])
    print(f"✅ File saved as {filename}")

    responder = FileTransferResponder(listener)
    confirm_msg = responder.confirm_file_received(
        to_ip=buffer["sender_ip"],
        from_user=buffer["to_user"],
        to_user=buffer["from_user"],
        file_id=file_id
    )
    msg_str = "\n".join(f"{k}: {v}" for k, v in confirm_msg.items()) + "\n\n"
    listener.send_unicast(msg_str, buffer["sender_ip"])
