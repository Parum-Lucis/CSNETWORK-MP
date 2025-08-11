import config
from utils.message_builder import generate_message_id, format_message_dict
from utils.time_utils import current_unix_time
from utils.token_utils import generate_token
from utils.printer import verbose_log, notif_log
from storage.user_followers import add_following, remove_following

def build_follow_msg(local_user_id: str, target_user_id: str, action: str):

    return {
        "TYPE": action,
        "MESSAGE_ID": generate_message_id(),
        "FROM": local_user_id,
        "TO": target_user_id,
        "TIMESTAMP": current_unix_time(),
        "TOKEN": generate_token(local_user_id, 3600, "follow"),
    }

def follow_user(profile, peer, udp):
    msg = build_follow_msg(profile.user_id, peer.user_id, "FOLLOW")
    udp.send_unicast(format_message_dict(msg), peer.ip)
    add_following(peer.user_id)
    notif_log(f"You followed {peer.user_id}")
    verbose_log("FOLLOW >", f"{profile.user_id} followed {peer.user_id} - {current_unix_time()}")

def unfollow_user(profile, peer, udp):
    msg = build_follow_msg(profile.user_id, peer.user_id, "UNFOLLOW")
    udp.send_unicast(format_message_dict(msg), peer.ip)
    remove_following(peer.user_id)
    notif_log(f"You unfollowed {peer.user_id}")
    verbose_log("UNFOLLOW >", f"{profile.user_id} unfollowed {peer.user_id} - {current_unix_time()}")