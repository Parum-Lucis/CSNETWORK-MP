from storage.peer_directory import update_peer_last_seen
from core.token_validator import validate_token
from utils.printer import verbose_log

def handle_ping(msg: dict, addr):
    user_id = msg.get("USER_ID")
    token = msg.get("TOKEN")
    if not validate_token(token, expected_scope="ping"):
        verbose_log("DROP", f"Invalid ping from {user_id}")
        return
    update_peer_last_seen(user_id)
    verbose_log("PING", f"Ping received from {user_id} ({addr[0]})")