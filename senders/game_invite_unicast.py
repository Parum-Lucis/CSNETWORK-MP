# game_invite_unicast.py

import time
import uuid
import random
from utils.token_utils import generate_token
from utils.printer import verbose_log
from storage.peer_directory import get_peer


def build_tictactoe_invite(profile, to_user_id, symbol=None):
    """
    Build a TICTACTOE_INVITE message.

    Args:
        profile (Profile): The local profile sending the invite.
        to_user_id (str): The target peer's user ID (name@ip).
        symbol (str): Optional symbol ("X" or "O"). Random if None.

    Returns:
        str: The RFC-compliant LSNP message.
    """
    if symbol not in ["X", "O"]:
        symbol = random.choice(["X", "O"])  # Randomly assign if not provided

    game_id = f"g{random.randint(0, 255)}"  # gX format
    message_id = uuid.uuid4().hex[:8]       # short unique ID

    token = generate_token(profile.user_id, ttl=3600, scope="game")

    return "\n".join([
        "TYPE: TICTACTOE_INVITE",
        f"FROM: {profile.user_id}",
        f"TO: {to_user_id}",
        f"GAMEID: {game_id}",
        f"MESSAGE_ID: {message_id}",
        f"SYMBOL: {symbol}",
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {token}",
        ""
    ])


def invite_peer_to_game(profile, udp_listener, to_user_id):
    """
    Sends a Tic Tac Toe game invite to a peer.

    Args:
        profile (Profile): The sender's profile.
        udp_listener (UDPListener): UDP listener to send messages.
        to_user_id (str): Target peer's user ID.
    """
    peer = get_peer(to_user_id)
    if not peer:
        print(f"⚠ Peer {to_user_id} not found or offline.")
        return

    # Build message
    msg = build_tictactoe_invite(profile, to_user_id)

    # Send unicast to peer's IP
    udp_listener.send_unicast(msg, peer.ip)

    verbose_log("[GAME]", f"Sent Tic Tac Toe invite to {to_user_id}")
    print(f"🎮 {profile.display_name} is inviting {to_user_id} to play tic-tac-toe.")
