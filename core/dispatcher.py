from handlers.ack_handler import handle_ack
from handlers.group_handler import handle_group_message, handle_group_create, handle_group_update
from handlers.ping_handler import handle_ping
from handlers.file_handler import handle_file
from handlers.profile_handler import handle_profile
from handlers.like_handler import handle_like
from handlers.post_handler import handle_post
from handlers.direct_message_handler import handle_dm
from utils.network_utils import verify_sender_ip
from utils.printer import verbose_log

# Import revoke handler and cleanup
from handlers.revoke_handler import handle_revoke
from core.token_validator import cleanup_revoked_tokens

def parse_message(message: str) -> dict:
    """
    Parses a raw LSNP key-value message string into a dictionary.
    """
    lines = message.strip().split("\n")
    msg_dict = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            msg_dict[key.strip()] = value.strip()
    return msg_dict


class Dispatcher:
    """
    Routes parsed LSNP messages to the correct handler based on TYPE.
    """

    def __init__(self, listener, local_profile):
        self.listener = listener
        self.local_profile = local_profile

    def handle(self, raw_message: str, addr):
        """
        Main entry point for handling all incoming UDP messages.
        """
        verbose_log("RECV <", raw_message)

        msg = parse_message(raw_message)
        msg_type = msg.get("TYPE")

        # Optional IP verification (disabled in current version)
        """
        if not verify_sender_ip(msg, addr):
            verbose_log("DROP!", f"IP mismatch: FROM={msg.get('FROM')} actual={addr[0]}")
            return
        """

        # Route based on TYPE
        if msg_type == "PROFILE":
            handle_profile(msg, addr)
        elif msg_type == "POST":
            handle_post(msg, addr)
        elif msg_type == "DM":
            handle_dm(msg, addr)
        elif msg_type == "ACK":
            handle_ack(msg, addr)
        elif msg_type == "PING":
            handle_ping(msg, addr)
        elif msg_type == "GROUP_CREATE":
            handle_group_create(msg, addr)
        elif msg_type == "GROUP_UPDATE":
            handle_group_update(msg, addr)
        elif msg_type == "GROUP_MESSAGE":
            handle_group_message(msg, addr)
        elif msg_type in ("FILE_OFFER", "FILE_CHUNK", "FILE_RECEIVED"):
            handle_file(msg, addr, self.listener, self.local_profile)
        elif msg_type == "LIKE":
            handle_like(msg, addr)
        elif msg_type == "REVOKE":
            handle_revoke(msg, addr)
        else:
            verbose_log("WARN", f"Unknown TYPE: {msg_type}")

        # Clean up expired revoked tokens every time a message is handled
        cleanup_revoked_tokens()
