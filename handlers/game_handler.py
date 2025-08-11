import time
import questionary

from core import ack_registry
from core.ack_registry import register_ack
from core.token_validator import validate_token
from utils.printer import verbose_log, notif_log, clear_screen
from queue import Queue
from models import game_session

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

    pending_game_invites.put((msg, addr, udp_listener, local_profile))

def process_game_invite(msg, addr, listener, local_profile):
    from_user = msg.get("FROM")
    game_id = msg.get("GAMEID")
    symbol = msg.get("SYMBOL")
    message_id = msg.get("MESSAGE_ID")

    notif_log(f"{from_user} is inviting you to play tic-tac-toe.")

    clear_screen()

    accept = questionary.confirm(
        f"{from_user} invited you to play tic-tac-toe as '{symbol}'. Accept?"
    ).ask()

    if accept:
        # Define what to do when ACK response is received
        def on_ack(ack):
            ack_msg = "\n".join(f"{k}: {v}" for k, v in ack.items()) + "\n\n"
            listener.send_unicast(ack_msg, addr[0])
            notif_log(f"✅ You accepted the invite from {from_user}")

        # Register the ACK callback by message_id
        register_ack(message_id, on_ack)

        # Now actually send the ACK back to the inviter
        ack_responder = GameInviteResponder(listener)
        ack_responder.send_ack(addr[0], message_id, status="ACCEPTED")

        from models import game_session
        game_session.start_game(local_profile, listener, game_id, from_user, symbol, first_turn=False)

    else:
        notif_log(f"❌ You declined the invite from {from_user}")

def handle_move(msg, addr, listener, local_profile):
    position = int(msg.get("POSITION"))
    symbol = msg.get("SYMBOL")
    game_id = msg.get("GAMEID")
    turn = int(msg.get("TURN"))

    game_session.apply_move(game_id, position, symbol)

def handle_game_ack(msg, addr, listener, local_profile):
    # Called when ACK received for game invite
    if msg.get("STATUS") == "ACCEPTED":
        game_id = msg.get("GAMEID")  # we’d store this in invite context
        symbol = msg.get("SYMBOL")
        opponent_id = msg.get("FROM")
        game_session.start_game(local_profile, listener, game_id, opponent_id, symbol, first_turn=False)