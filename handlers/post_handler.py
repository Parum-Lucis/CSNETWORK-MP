from utils.printer import verbose_log
from core.token_validator import validate_token

def handle_post(msg: dict, addr):
    """
    Handles a POST message where peer broadcasts to followers

    Args:
        msg (dict): the post message
        addr (tuple): the sender's address
    """
    token = msg.get("TOKEN")
    user_id = msg.get("USER_ID")
    content = msg.get("CONTENT")

    if not validate_token(token, expected_scope="broadcast"):
        verbose_log("DROP!", f"Invalid token for POST from {user_id}")
        return

    display_name = user_id.split("@")[0]
    print(f"{display_name}: {content}")
    verbose_log("INFO", f"POST received from {user_id} at {addr[0]}")