import time
import questionary
from core.token_validator import validate_token
from utils.printer import verbose_log, notif_log

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
    from_user = msg.get("FROM")
    token = msg.get("TOKEN")
    symbol = msg.get("SYMBOL")
    game_id = msg.get("GAMEID")
    message_id = msg.get("MESSAGE_ID")

    # ✅ Validate token scope
    if not validate_token(token, scope="game"):
        verbose_log("DROP!", f"Invalid game token frum {from_user}")
        return

    # ✅ Log and notify
    display_name = from_user.split("@")[0]
    notif_log(f"{display_name} is inviting you to play tic-tac-toe.")
    verbose_log("GAME_INVITE", f"Invite from {from_user} for game {game_id} as '{symbol}'")

    # ✅ UI Prompt
    accept = questionary.confirm(
        f"{display_name} invited you to play tic-tac-toe.\n"
        f"You will play as '{symbol}'. Accept?"
    ).ask()

    if accept:
        responder = GameInviteResponder(udp_listener)
        target_ip = from_user.split("@")[1]
        responder.send_ack(target_ip, message_id, status="ACCEPTED")
        verbose_log("GAME_INVITE", f"Accepted invite from {from_user} for game {game_id}")
    else:
        verbose_log("GAME_INVITE", f"Declined invite from {from_user} for game {game_id}")
