import config
from utils.message_builder import generate_message_id, format_message_dict
from utils.token_utils import generate_token
from utils.time_utils import current_unix_time
from core.ack_registry import register_ack
from utils.printer import verbose_log, notif_log
from storage.dm_store import save_dm

def send_dm(profile, peer, content: str, udp):
    message_id = generate_message_id()
    token = generate_token(profile.user_id, config.TOKEN_TTL_CHAT, "chat")
    timestamp = current_unix_time()

    dm = {
        "TYPE": "DM",
        "FROM": profile.user_id,
        "TO": peer.user_id,
        "CONTENT": content,
        "TIMESTAMP": timestamp,
        "MESSAGE_ID": message_id,
        "TOKEN": token
    }

    dm_dict = format_message_dict(dm)
    udp.send_unicast(dm_dict, peer.ip)
    save_dm(dm)

    notif_log(f"{profile.user_id} sent DM to {peer.user_id}")
    verbose_log("DM", f"{profile.user_id} sent DM: '{content}' to {peer.user_id} - {current_unix_time()}")

    def on_ack():
        notif_log(f"{profile.user_id} delivered DM to {peer.user_id}")

    register_ack(message_id, on_ack)