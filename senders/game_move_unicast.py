import time
import uuid
from utils.token_utils import generate_token

def send_game_move(profile, listener, game_id, to_user_id, position, symbol, turn):
    """
    Sends a Tic Tac Toe move to the opponent.
    """
    token = generate_token(profile.user_id, ttl=1728943600, scope="game")
    message_id = uuid.uuid4().hex[:8]

    move_msg = "\n".join([
        "TYPE: TICTACTOE_MOVE",
        f"FROM: {profile.user_id}",
        f"TO: {to_user_id}",
        f"GAMEID: {game_id}",
        f"MESSAGE_ID: {message_id}",
        f"POSITION: {position}",
        f"SYMBOL: {symbol}",
        f"TURN: {turn}",
        f"TOKEN: {token}",
        ""
    ])
    to_ip = to_user_id.split("@")[1]
    listener.send_unicast(move_msg, to_ip)
