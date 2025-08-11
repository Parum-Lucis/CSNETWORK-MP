import config
from utils.time_utils import current_unix_time
from utils.token_utils import generate_token
from utils.message_builder import format_message_dict
from utils.printer import verbose_log, notif_log
from storage.likes_store import add_like, remove_like

def build_like(from_user_id: str, to_user_id: str, post_ts: int, action: str):
    return {
        "TYPE": "LIKE",
        "FROM": from_user_id,
        "TO": to_user_id,
        "POST_TIMESTAMP": int(post_ts),
        "ACTION": action,           
        "TIMESTAMP": current_unix_time(),
        "TOKEN": generate_token(from_user_id, config.TOKEN_TTL_BROADCAST, "broadcast"),
    }

def send_like(profile, post: dict, udp, action: str = "LIKE"):
    to_user = post.get("USER_ID")
    post_ts = post.get("TIMESTAMP")

    msg = build_like(profile.user_id, to_user, post_ts, action)
    msg_str = format_message_dict(msg)

    udp.send_broadcast(msg_str)

    if action == "LIKE":
        add_like(to_user, int(post_ts), profile.user_id)
        verbose_log("LIKE", f"{msg.get("FROM")} Liked post {msg.get("POST_TIMESTAMP")} by {msg.get("TO")} - {current_unix_time()}")
        notif_log(f"{msg.get("FROM")} Liked post {msg.get("POST_TIMESTAMP")} by {msg.get("TO")}")
    else:
        remove_like(to_user, int(post_ts), profile.user_id)
        verbose_log("LIKE", f"{msg.get("FROM")} Unliked post {msg.get("POST_TIMESTAMP")} by {msg.get("TO")} - {current_unix_time()}")
        notif_log(f"{msg.get("FROM")} Unliked post {msg.get("POST_TIMESTAMP")} by {msg.get("TO")}")

