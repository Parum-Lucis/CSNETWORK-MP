"""Handlers for TicTacToe messages (RFC 5.12-5.14).

Validations:
 - `TO` matches local_profile.user_id
 - IP in FROM field matches UDP source (if provided in FROM)
 - Token is validated via core.token_validator.validate_token(token, scope='game')
"""
from storage.game_directory import create_session, get_session, update_session_last_seen, remove_session
from models.game_session import GameSession
from utils.printer import verbose_log
from senders.game_responder import GameResponder
from core.token_validator import validate_token
import queue

# UI queues for non-blocking notifications; CLI will read from these
try:
    from ui.cli import pending_game_invites, pending_game_logs
except Exception:
    pending_game_invites = queue.Queue()
    pending_game_logs = queue.Queue()


def _verify_from_ip(msg_from_field: str, addr_ip: str) -> bool:
    if "@" in msg_from_field:
        _, ip = msg_from_field.rsplit("@", 1)
        return ip == addr_ip
    return True


def _generate_local_ip_from_profile(user_id: str) -> str:
    if "@" in user_id:
        return user_id.rsplit("@", 1)[1]
    return "127.0.0.1"


def handle_tictactoe_invite(msg: dict, addr: tuple, listener, local_profile):
    """Process TICTACTOE_INVITE."""
    if msg.get("TO") != local_profile.user_id:
        return

    if not _verify_from_ip(msg.get("FROM", ""), addr[0]):
        verbose_log("WARN", f"TICTACTOE_INVITE FROM IP mismatch: {msg.get('FROM')} vs {addr[0]}")
        return

    token = msg.get("TOKEN")
    if not validate_token(token, scope="game"):
        verbose_log("WARN", f"Invalid/expired token for TICTACTOE_INVITE from {msg.get('FROM')}")
        return

    gameid = msg.get("GAMEID")
    inviter = msg.get("FROM")
    symbol = (msg.get("SYMBOL") or "X").upper()

    # Determine players & IPs: inviter is msg['FROM'] (address in FROM),
    # invitee is local_profile
    if symbol == "X":
        p_x, p_o = inviter, local_profile.user_id
        px_ip, po_ip = addr[0], local_profile.ip
    else:
        p_x, p_o = local_profile.user_id, inviter
        px_ip, po_ip = local_profile.ip, addr[0]

    session = GameSession(game_id=gameid, player_x=p_x, player_o=p_o, player_x_ip=px_ip, player_o_ip=po_ip)
    session.assign_symbols(inviter, symbol)
    created = create_session(session)
    if not created:
        update_session_last_seen(gameid)

    pending_game_invites.put((msg, addr))
    verbose_log("INFO", f"Received TicTacToe invite {gameid} from {inviter}")

    # Send plain ACK for receipt (other parts of app use simple ACK messages)
    ack_msg = f"TYPE: ACK\nMESSAGE_ID: {msg.get('MESSAGE_ID')}\nSTATUS: RECEIVED\n\n"
    listener.send_unicast(ack_msg, addr[0])


def handle_tictactoe_move(msg: dict, addr: tuple, listener, local_profile):
    """Process TICTACTOE_MOVE."""
    if msg.get("TO") != local_profile.user_id:
        return

    if not _verify_from_ip(msg.get("FROM", ""), addr[0]):
        verbose_log("WARN", f"TICTACTOE_MOVE FROM IP mismatch: {msg.get('FROM')} vs {addr[0]}")
        return

    token = msg.get("TOKEN")
    if not validate_token(token, scope="game"):
        verbose_log("WARN", f"Invalid/expired token for TICTACTOE_MOVE from {msg.get('FROM')}")
        return

    gameid = msg.get("GAMEID")
    session = get_session(gameid)
    if not session:
        pending_game_logs.put(f"⚠️ Received move for unknown game {gameid}")
        return

    try:
        position = int(msg.get("POSITION"))
        turn_num = int(msg.get("TURN"))
        symbol = (msg.get("SYMBOL") or "").upper()
    except Exception:
        pending_game_logs.put("⚠️ Invalid TicTacToe move message fields")
        return

    # Duplicate detection (idempotent)
    if turn_num in session.processed_turns:
        ack_msg = f"TYPE: ACK\nMESSAGE_ID: {msg.get('MESSAGE_ID')}\nSTATUS: DUPLICATE\n\n"
        listener.send_unicast(ack_msg, addr[0])
        return

    # Expected turn number
    if turn_num != session.turn + 1:
        pending_game_logs.put(f"⚠️ Unexpected TURN {turn_num} for game {gameid} (expected {session.turn + 1})")
        ack_msg = f"TYPE: ACK\nMESSAGE_ID: {msg.get('MESSAGE_ID')}\nSTATUS: INVALID_TURN\n\n"
        listener.send_unicast(ack_msg, addr[0])
        return

    applied = session.apply_move(user_id=msg.get("FROM"), position=position, symbol=symbol, turn_number=turn_num)
    if not applied:
        pending_game_logs.put(f"⚠️ Invalid move by {msg.get('FROM')} in game {gameid} at pos {position}")
        ack_msg = f"TYPE: ACK\nMESSAGE_ID: {msg.get('MESSAGE_ID')}\nSTATUS: INVALID_MOVE\n\n"
        listener.send_unicast(ack_msg, addr[0])
        return

    # ACK
    ack_msg = f"TYPE: ACK\nMESSAGE_ID: {msg.get('MESSAGE_ID')}\nSTATUS: RECEIVED\n\n"
    listener.send_unicast(ack_msg, addr[0])

    # Check for win/draw; if so, send RESULT to opponent
    outcome = session.check_winner()
    if outcome:
        if outcome.get("result") == "WIN":
            session.status = "COMPLETE"
            session.winner = outcome.get("winner")
            session.winning_line = outcome.get("line")
            opponent = session.other_player(msg.get("FROM"))
            opponent_ip = _generate_local_ip_from_profile(opponent)
            responder = GameResponder(listener, session.other_player(msg.get("FROM")), opponent_ip)
            # Use GameResponder with local_profile info: we need local user id and IP.
            # We will call send_result using local_profile id; caller (Dispatcher) passes listener & local_profile.
            responder = GameResponder(listener, local_profile.user_id, local_profile.ip)
            responder.send_result(
                to_ip=opponent_ip,
                to_user=opponent,
                game_id=session.game_id,
                result="WIN",
                symbol=outcome.get("symbol"),
                winning_line=outcome.get("line"),
            )
        elif outcome.get("result") == "DRAW":
            session.status = "COMPLETE"
            opponent = session.other_player(msg.get("FROM"))
            opponent_ip = _generate_local_ip_from_profile(opponent)
            responder = GameResponder(listener, local_profile.user_id, local_profile.ip)
            responder.send_result(
                to_ip=opponent_ip,
                to_user=opponent,
                game_id=session.game_id,
                result="DRAW",
                symbol=symbol,
                winning_line=None,
            )

    update_session_last_seen(gameid)
    pending_game_logs.put(f"Move applied for game {gameid} at position {position} (turn {turn_num})")


def handle_tictactoe_result(msg: dict, addr: tuple, listener, local_profile):
    """Process TICTACTOE_RESULT."""
    if msg.get("TO") != local_profile.user_id:
        return

    if not _verify_from_ip(msg.get("FROM", ""), addr[0]):
        verbose_log("WARN", f"TICTACTOE_RESULT FROM IP mismatch: {msg.get('FROM')} vs {addr[0]}")
        return

    token = msg.get("TOKEN")
    # RESULT messages in RFC examples didn't include TOKEN in your last example, but if present validate it:
    if token and not validate_token(token, scope="game"):
        verbose_log("WARN", f"Invalid/expired token for TICTACTOE_RESULT from {msg.get('FROM')}")
        return

    gameid = msg.get("GAMEID")
    session = get_session(gameid)
    if not session:
        pending_game_logs.put(f"⚠️ Received result for unknown game {gameid}")
        return

    result = msg.get("RESULT")
    symbol = msg.get("SYMBOL")
    winning_line_raw = msg.get("WINNING_LINE")
    winning_line = [int(i) for i in winning_line_raw.split(",")] if winning_line_raw else None

    session.status = "COMPLETE"
    session.winner = None
    if result == "WIN" and winning_line:
        session.winning_line = winning_line
        # find winner user id
        for uid, sym in session.symbol_of.items():
            if sym == symbol:
                session.winner = uid
                break

    pending_game_logs.put(f"Game {gameid} finished with result: {result}")
    remove_session(gameid)
