"""
core/revoke_handler.py

Handles incoming REVOKE messages from peers.
Adds revoked tokens to the local revocation list.
"""

from utils.token_utils import revoke_token
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
        verbose_log("RECV <", f"Revoked token from {addr[0]}: {token}")
