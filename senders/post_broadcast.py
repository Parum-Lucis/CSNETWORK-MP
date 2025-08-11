import config
from utils.message_builder import generate_message_id, format_message_dict
from utils.token_utils import generate_token
from storage.post_store import save_post
from utils.printer import verbose_log
from utils.time_utils import current_unix_time

def send_post(profile, content: str, udp):
    message_id = generate_message_id()
    token = generate_token(profile.user_id, config.token_ttl_post, "broadcast")

    post = {
        "TYPE": "POST",
        "USER_ID": profile.user_id,
        "CONTENT": content,
        "TTL": config.token_ttl_post,
        "TIMESTAMP": current_unix_time(),
        "MESSAGE_ID": message_id,
        "TOKEN": token
    }

    verbose_log("POST", f"Post uploaded by {profile.user_id}: {content} - {current_unix_time()}")
    print(f"\n\nPost uploaded by {profile.user_id}: {content}\n\n")

    post_dict = format_message_dict(post)
    udp.send_broadcast(post_dict)
