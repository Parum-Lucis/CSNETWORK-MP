import os
import base64
from models.file_transfer import FileTransferResponder
from ui.cli import flush_pending_logs, pending_file_offers, pending_logs  # import both queues
from utils.printer import NOTIFICATIONS
file_buffer = {}

def handle_file(msg: dict, addr: tuple, listener, local_profile):
    """
    Handles file-related messages. Non-blocking — file offers go to queue.
    """
    msg_type = msg["TYPE"]
    file_id = msg.get("FILEID")
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    ip = addr[0]

    responder = FileTransferResponder(listener)

    if to_user != local_profile.user_id:
        return None
    
    if msg_type == "FILE_OFFER":
        pending_file_offers.put((msg, addr))
        file_buffer[file_id] = {
            "filename": "received_" + msg["FILENAME"],
            "chunks": {},
            "total_chunks": 0,
            "from_user": from_user,
            "to_user": to_user,
            "sender_ip": ip,
            "original_message_id": msg["FILEID"]
        }

    elif msg_type == "FILE_CHUNK":
        if file_id not in file_buffer:
            NOTIFICATIONS.append("⚠️ Received chunk for unknown file")
            return

        file_buffer[file_id]["total_chunks"] = int(msg["TOTAL_CHUNKS"])
        chunk_num = int(msg["CHUNK_INDEX"])
        data = base64.b64decode(msg["DATA"])
        file_buffer[file_id]["chunks"][chunk_num] = data

        if len(file_buffer[file_id]["chunks"]) == file_buffer[file_id]["total_chunks"]:
            save_chunks(file_id, file_buffer[file_id], listener)

    elif msg_type == "FILE_RECEIVED":
        NOTIFICATIONS.append(f"✅ Peer confirmed file {msg.get('FILEID')} was saved (STATUS: {msg.get('STATUS')}).")

    elif msg_type == "ACK":
        NOTIFICATIONS.append(f"📨 ACK from {from_user}: {msg['STATUS']} for {msg['MESSAGE_ID']}")

def save_chunks(file_id, buffer, listener):
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    filename = os.path.join(downloads_dir, buffer["filename"])
    with open(filename, "wb") as f:
        for i in sorted(buffer["chunks"]):
            f.write(buffer["chunks"][i])

    # Add to log queue
    NOTIFICATIONS.append(f"✅ File transfer of {filename} is complete")

    # Send FILE_RECEIVED confirmation
    responder = FileTransferResponder(listener)
    responder.confirm_file_received(
        to_ip=buffer["sender_ip"],
        from_user=buffer["to_user"],
        to_user=buffer["from_user"],
        file_id=file_id
    )

    # Immediately flush so user sees it now
    flush_pending_logs()