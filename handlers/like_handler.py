from core.token_validator import validate_token, parse_token
from utils.printer import verbose_log, notif_log
from utils.time_utils import current_unix_time
from storage.post_store import has_post
from storage.likes_store import add_like, remove_like

def handle_like(msg, addr):
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    post_ts = msg.get("POST_TIMESTAMP")
    action = (msg.get("ACTION") or "").upper()
    token = msg.get("TOKEN")

    if not validate_token(token, "broadcast"):
        verbose_log("DROP!", f"Expired like token, invalid from {from_user} to post {post_ts} by {to_user} - {current_unix_time}")
        notif_log(f"Expired liked token from {from_user}")
        return

    token_user, _, _ = parse_token(token)
    if token_user != from_user:
        verbose_log("DROP!", f"Like token user '{token_user}' != From user '{from_user}' - {current_unix_time()}")
        notif_log("Token and from user mismatch")
        return

    if action not in ("LIKE", "UNLIKE"):
        verbose_log("DROP!", f"Like unknown action: '{action}' from {from_user} - {current_unix_time()}")
        notif_log(f"Like unknown action: '{action}' from {from_user}")
        return
    
    post_ts_i = int(post_ts)
    if not has_post(to_user, post_ts_i):
        verbose_log("LIKE", f"Ignored like for unknown post {post_ts_i} -> {to_user} - {current_unix_time()}")
        notif_log(f"Ignored like for unknown post {post_ts_i} -> {to_user}")
        return
    
    if action == "LIKE":
        add_like(to_user, post_ts_i, from_user)
        verbose_log("LIKE", f"{from_user} liked post {post_ts_i} by {to_user} - {current_unix_time()}")
        notif_log(f"{from_user} liked post by {to_user}")
    else:
        remove_like(to_user, post_ts_i, from_user)
        verbose_log("LIKE", f"{from_user} unliked post {post_ts_i} by {to_user} - {current_unix_time()}")
        notif_log(f"{from_user} unliked post by {to_user}")
