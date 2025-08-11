from core.token_validator import validate_token, parse_token
from storage.dm_store import save_dm
from utils.printer import verbose_log, notif_log
from core.udp_singleton import get_udp_listener
from utils.message_builder import build_ack_for
from utils.time_utils import current_unix_time

def parse_user_id_ip(user_id: str):
    name, ip = user_id.split("@", 1)
    return name, ip
    
def handle_dm(msg, addr):
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    content = msg.get("CONTENT")
    timestamp = msg.get("TIMESTAMP")
    token = msg.get("TOKEN")
    message_id = msg.get("MESSAGE_ID")

    if not validate_token(token, "chat"):
        verbose_log("DROP!", f"Expired/Rejected DM sent by {from_user}: {content} - {current_unix_time()}")
        notif_log(f"Expired/Rejected DM sent by {from_user}: {content}")
        return
    
    token_user,_,_ = parse_token(token)
    if token_user != from_user:
        verbose_log("DROP!", f"Token user '{token_user}' != DM sender '{from_user}' - {current_unix_time()}")
        notif_log(f"Token and DM sender mismatch")
        return
    
    # _, declared_ip = parse_user_id_ip(from_user)
    # if declared_ip and declared_ip != addr[0]:
    #     verbose_log("DROP!", f"DM Sender IP mismatch: declared {declared_ip}, src {addr[0]} - {current_unix_time()}")
    #     print(f"\n\nDM Sender IP mismatch\n\n")
    
    status = save_dm(msg)

    if status:
        verbose_log("DM", f"Received DM sent by {from_user}: {content} - {current_unix_time()}")
        notif_log(f"DM received from {from_user}: {content}")
    else:
        verbose_log("DROP!", f"Duplicated/seen DM sent by {from_user} (ignored): {content} - {current_unix_time()}")
        notif_log(f"DM duplicated/seen from {from_user}: {content}")

    udp = get_udp_listener()
    ack_str = build_ack_for(message_id, to_user)
    udp.send_unicast(ack_str, addr[0])