import os
import base64
from models.file_transfer import FileTransferResponder
from ui.cli import pending_file_offers  # shared queue

file_buffer = {}

def handle_file(msg: dict, addr: tuple, listener):
    """
    Handles file-related messages (excluding ACK — handled by ack_handler).
    """
    msg_type = msg["TYPE"]
    file_id = msg.get("FILEID")
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    ip = addr[0]

    if msg_type == "FILE_OFFER":
        # Queue for CLI to handle user prompt
        pending_file_offers.put((msg, addr))

        file_buffer[file_id] = {
            "filename": "received_" + msg["FILENAME"],
            "chunks": {},
            "total_chunks": 0,  # unknown until first chunk arrives
            "from_user": from_user,
            "to_user": to_user,
            "sender_ip": ip,
            "original_message_id": msg["MESSAGE_ID"]
        }

    elif msg_type == "FILE_CHUNK":
        if file_id not in file_buffer:
            print("⚠️ Received chunk for unknown file")
            return

        # Update total_chunks dynamically
        file_buffer[file_id]["total_chunks"] = int(msg["TOTAL_CHUNKS"])

        chunk_num = int(msg["CHUNK_INDEX"])
        data = base64.b64decode(msg["DATA"])
        file_buffer[file_id]["chunks"][chunk_num] = data

        # Check if all chunks received
        if len(file_buffer[file_id]["chunks"]) == file_buffer[file_id]["total_chunks"]:
            save_chunks(file_id, file_buffer[file_id], listener)

    elif msg_type == "FILE_RECEIVED":
        print(f"✅ Peer confirmed file {msg.get('FILEID')} was saved (STATUS: {msg.get('STATUS')}).")


def save_chunks(file_id, buffer, listener):
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    filepath = os.path.join(downloads_dir, buffer["filename"])
    with open(filepath, "wb") as f:
        for i in sorted(buffer["chunks"]):
            f.write(buffer["chunks"][i])

    print(f"✅ File saved as {filepath}")

    responder = FileTransferResponder(listener)
    responder.confirm_file_received(
        to_ip=buffer["sender_ip"],
        from_user=buffer["to_user"],
        to_user=buffer["from_user"],
        file_id=file_id
    )
