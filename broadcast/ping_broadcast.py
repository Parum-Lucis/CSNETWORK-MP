import threading
import time
from config import BROADCAST_INTERVAL
from utils.token_utils import generate_token
from utils.printer import verbose_log

def build_ping_message(user_id: str) -> str:
    """
    Builds a LSNP PING message string with a fresh token.
    """
    token = generate_token(user_id, ttl=BROADCAST_INTERVAL + 5, scope="ping")
    return f"TYPE: PING\nUSER_ID: {user_id}\nTOKEN: {token}\n\n"

def start_broadcast(user_id: str, udp_sender):
    """
    Starts periodic PING broadcasts.
    """
    def loop():
        while True:
            msg = build_ping_message(user_id)
            udp_sender.send_broadcast(msg)
            verbose_log("BROADCAST", "Sent PING broadcast")
            time.sleep(BROADCAST_INTERVAL)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()