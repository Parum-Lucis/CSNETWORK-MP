from utils.printer import verbose_log
from core.ack_registry import resolve_ack

def handle_ack(msg: dict, addr: tuple):
    """
    Handles ACK messages.
    ACK format:
        TYPE: ACK
        MESSAGE_ID: <original message id>
        STATUS: RECEIVED
    """
    message_id = msg.get("MESSAGE_ID")
    status = msg.get("STATUS")

    if not message_id or not status:
        verbose_log("ACK", "Malformed ACK message received.")
        return

    verbose_log("ACK", f"Received ACK for {message_id} with status {status} from {addr[0]}")

    if resolve_ack(message_id):
        print("Resolving ACK")
        verbose_log("ACK", f"ACK resolved and callback executed for {message_id}")
    else:
        verbose_log("ACK", f"No pending ACK for {message_id}")



# def handle_ack(msg: dict, addr):
#     user_id = msg.get("USER_ID")
#     message_id = msg.get("MESSAGE_ID")
#     pending_acks
#     ack_type = msg.get("ACK_TYPE")

#     if message_id in pending_acks:
#         pending_acks[message_id]["on_ack"]()  # e.g., file_transfer.file_transmit()
#         del pending_acks[message_id]

#     if user_id and ack_type:
#         verbose_log("ACK", f"Received ACK from {user_id} for {ack_type}")
#         if ack_type == "ACCEPTED":
#             pass
                            