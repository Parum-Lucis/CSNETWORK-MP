import uuid

def generate_message_id() -> str:
    """
    Generates a unique message ID using UUID4.

    This ID can be used to track LSNP messages, prevent duplicates,
    or reference messages in replies.

    Returns:
        str: A 32-character hexadecimal string (e.g., '3f9c7e3c6d2a49e9a142d01f1b325c90')

    Note: AI-generated code
    """
    return uuid.uuid4().hex

# def build_ack_message(user_id: str, message_type: str) -> str:
#     return f"TYPE: ACK\nUSER_ID: {user_id}\nACK_TYPE: {message_type}\n\n"

def build_ack_for(original_message_id: str, user_id: str):
    ack = {
        "TYPE": "ACK",
        "USER_ID": user_id,
        "MESSAGE_ID": original_message_id,
        "STATUS": "RECEIVED"
    }

    return format_message_dict(ack)

def format_message_dict(message_dict: dict):
    return "\n".join(f"{k}: {v}" for k, v in message_dict.items()) + "\n\n"
