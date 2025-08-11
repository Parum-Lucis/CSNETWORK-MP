import time
import questionary
from core.token_validator import validate_token
from utils.printer import verbose_log, notif_log
from queue import Queue

pending_game_invites = Queue()

class GameInviteResponder:
    def __init__(self, listener):
        self.listener = listener

    def send_ack(self, to_ip, message_id, status="ACCEPTED"):
        """
        Sends an ACK message to confirm acceptance of a game invite.
        """
        ack = {
            "TYPE": "ACK",
            "MESSAGE_ID": message_id,
            "STATUS": status
        }
        msg = "\n".join(f"{k}: {v}" for k, v in ack.items()) + "\n\n"
        self.listener.send_unicast(msg, to_ip)


def handle_invite(msg, addr, udp_listener, local_profile):
    """
    Handles incoming Tic Tac Toe game invites.
    Prompts user to accept or decline. Accept → Send ACK, Decline → do nothing.
    """
    to_user = msg.get("TO")

    if to_user != local_profile.user_id:
        return None

    pending_game_invites.put((msg, addr, udp_listener))

def process_game_invite(msg, addr, listener):
    from_user = msg.get("FROM")
    game_id = msg.get("GAMEID")
    symbol = msg.get("SYMBOL")
    message_id = msg.get("MESSAGE_ID")

    notif_log(f"{from_user} is inviting you to play tic-tac-toe.")

    accept = questionary.confirm(
        f"{from_user} invited you to play tic-tac-toe as '{symbol}'. Accept?"
    ).ask()

    if accept:
        ack = {
            "TYPE": "ACK",
            "MESSAGE_ID": message_id,
            "STATUS": "ACCEPTED"
        }
        ack_msg = "\n".join(f"{k}: {v}" for k, v in ack.items()) + "\n\n"
        listener.send_unicast(ack_msg, addr[0])
        notif_log(f"✅ You accepted the invite from {from_user}")
    else:
        notif_log(f"❌ You declined the invite from {from_user}")