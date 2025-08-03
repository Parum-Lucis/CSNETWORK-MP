from utils.printer import verbose_log

def handle_ack(msg: dict, addr):
    user_id = msg.get("USER_ID")
    ack_type = msg.get("ACK_TYPE")

    if user_id and ack_type:
        verbose_log("ACK", f"Received ACK from {user_id} for {ack_type}")