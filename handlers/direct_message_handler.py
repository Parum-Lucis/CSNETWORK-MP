from utils.printer import verbose_log
from core.token_validator import validate_token


def handle_dm(msg: dict, addr):
    """
    Handles a DM message (direct message to a peer).

    Args:
        msg (dict): the direct message
        addr (IP, port): the peer's address
    """

    token = msg.get("TOKEN")
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    content = msg.get("CONTENT")

    if not validate_token(token, expected_scope="chat"):
        verbose_log("DROP!", f"Invalid token for DM from {from_user}")
        return

    sender_name = from_user.split("@")[0]
    print(f"💌 DM from {sender_name}: {content}")
    verbose_log("INFO", f"DM received from {from_user} at {addr[0]}")
    