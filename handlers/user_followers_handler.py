from core.token_validator import validate_token, parse_token
from utils.printer import verbose_log, notif_log
from utils.time_utils import current_unix_time
from storage.user_followers import add_follower, remove_follower

def common_checks(msg: dict, expected_type: str):
    if msg.get("TYPE") != expected_type:
        verbose_log("DROP!", f"Expected type '{expected_type}' != Received type '{msg.get('TYPE')}' - {current_unix_time()}")
        notif_log(f"{expected_type} != {msg.get('TYPE')}")
        return False, None, None

    token = msg.get("TOKEN")
    from_user = msg.get("FROM")
    to_user = msg.get("TO")

    if not validate_token(token, "follow"):
        verbose_log("DROP!", f"Invalid/expired {expected_type} token from {from_user} - {current_unix_time()}")
        notif_log(f"Invalid/expired {expected_type} token from {from_user}")
        return False, None, None
    
    token_user, _, _ = parse_token(token)
    if token_user != from_user:
        verbose_log("DROP!", f"{expected_type}: token user '{token_user}' != from '{from_user}'")
        notif_log("Token and message user mismatch")
        return False, None, None

    return True, from_user, to_user

def handle_follow(msg, addr):
    ok, from_user, to_user = common_checks(msg, "FOLLOW")
    if not ok:
        return

    add_follower(from_user)

    notif_log(f"{from_user} has followed you")
    verbose_log("FOLLOW <", f"{from_user} followed you - {current_unix_time()}")

def handle_unfollow(msg: dict, addr: tuple):
    ok, from_user, to_user = common_checks(msg, "UNFOLLOW")
    if not ok:
        return

    remove_follower(from_user)

    notif_log(f"{from_user} has unfollowed you")
    verbose_log("UNFOLLOW <", f"{from_user} unfollowed you @ {current_unix_time()}")