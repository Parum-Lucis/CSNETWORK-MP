from core.token_validator import revoke_token
from utils.printer import verbose_log


def handle_revoke(msg, addr):
    """
    Processes an incoming REVOKE message.

    Args:
        msg (dict): Parsed LSNP message dictionary.
        addr (tuple): (IP, port) of sender.
    """
    token = msg.get("TOKEN")
    if token:
        revoke_token(token)
        verbose_log("RECV <", f"REVOKE from {addr[0]}: TOKEN: {token}")
    else:
        verbose_log("DROP!", f"REVOKE from {addr[0]} missing TOKEN field")
