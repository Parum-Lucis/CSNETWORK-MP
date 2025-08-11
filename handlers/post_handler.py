from core.token_validator import validate_token, parse_token
from storage.user_followers import is_follower
from storage.post_store import save_post
from utils.printer import verbose_log
from utils.time_utils import current_unix_time

def parse_user_id_ip(user_id_str: str):
    name, ip = user_id_str.split("@", 1)
    return name, ip

def handle_post(msg, addr):
    poster_id = msg.get("USER_ID")
    token = msg.get("TOKEN")
    content = msg.get("CONTENT")
    message_id = msg.get("MESSAGE_ID")

    if not validate_token(token, "broadcast"):
        verbose_log("DROP!", f"Expired/Rejected post uploaded by {poster_id}: {content} - {current_unix_time()}")
        print(f"\n\nExpired/Rejected post uploaded by {poster_id}: {content}\n\n")
        return
    
    token_user,_,_ = parse_token(token)
    if token_user != poster_id:
        verbose_log("DROP!", f"Token user '{token_user}' != message user '{poster_id}' - {current_unix_time()}")
        print(f"\n\nToken and message user mismatch\n\n")
        return
    
    _, declared_ip = parse_user_id_ip(poster_id)
    if declared_ip and declared_ip != addr[0]:
        verbose_log("DROP!", f"Poster IP mismatch: declared {declared_ip}, src {addr[0]} - {current_unix_time()}")
        print(f"\n\nPoster IP mismatch\n\n")
        return
    
    # if not is_follower(poster_id):
    #     verbose_log("DROP!", f"Expired/Rejected post uploaded by {poster_id} (Not a Follower): {content} - {current_unix_time()}")
    #     print(f"\n\nReceiver is not a follower of Sender\n\n")
    #     return
    
    status = save_post(msg)

    if status:
        verbose_log("POST", f"Received post uploaded by {poster_id}: {content} - {current_unix_time()}")
        print(f"\n\nPost received from {poster_id}: {content}\n\n")
        return
    else:
        verbose_log("DROP!", f"Duplicated/seen post uploaded by {poster_id} (ignored): {content} - {current_unix_time()}")
        print(f"\n\nPost duplicated/seen from {poster_id}: {content}\n\n")
        return
