"""TicTacToe responder / sender helpers.

Creates RFC-compliant messages exactly as specified (no extra fields except optional WINNING_LINE).
"""
import time
import uuid
from typing import Optional
from utils.printer import verbose_log
from utils.token_utils import generate_token


class GameResponder:
    def __init__(self, listener, local_user_id: str, local_ip: str):
        self.listener = listener
        self.local_user_id = local_user_id
        self.local_ip = local_ip

    @staticmethod
    def _finalize(kv_pairs):
        return "\n".join(f"{k}: {v}" for k, v in kv_pairs) + "\n\n"

    def send_invite(self, to_ip: str, to_user: str, game_id: str, symbol: str, message_id: str = None, token_ttl: int = 600):
        mid = message_id or uuid.uuid4().hex[:8]
        ts = str(int(time.time()))
        token = generate_token(self.local_user_id, token_ttl, "game")
        kv = [
            ("TYPE", "TICTACTOE_INVITE"),
            ("FROM", self.local_user_id),
            ("TO", to_user),
            ("GAMEID", game_id),
            ("MESSAGE_ID", mid),
            ("SYMBOL", symbol),
            ("TIMESTAMP", ts),
            ("TOKEN", token),
        ]
        msg = self._finalize(kv)
        self.listener.send_unicast(msg, to_ip)
        verbose_log("SEND >", msg)
        return mid

    def send_move(self, to_ip: str, to_user: str, game_id: str, position: int, symbol: str, turn: int, message_id: str = None, token_ttl: int = 600):
        mid = message_id or uuid.uuid4().hex[:8]
        token = generate_token(self.local_user_id, token_ttl, "game")
        kv = [
            ("TYPE", "TICTACTOE_MOVE"),
            ("FROM", self.local_user_id),
            ("TO", to_user),
            ("GAMEID", game_id),
            ("MESSAGE_ID", mid),
            ("POSITION", str(position)),
            ("SYMBOL", symbol),
            ("TURN", str(turn)),
            ("TOKEN", token),
        ]
        msg = self._finalize(kv)
        self.listener.send_unicast(msg, to_ip)
        verbose_log("SEND >", msg)
        return mid

    def send_result(self, to_ip: str, to_user: str, game_id: str, result: str, symbol: str, winning_line: Optional[list] = None, message_id: str = None, token_ttl: int = 600):
        mid = message_id or uuid.uuid4().hex[:8]
        ts = str(int(time.time()))
        kv = [
            ("TYPE", "TICTACTOE_RESULT"),
            ("FROM", self.local_user_id),
            ("TO", to_user),
            ("GAMEID", game_id),
            ("MESSAGE_ID", mid),
            ("RESULT", result),
            ("SYMBOL", symbol),
        ]
        if winning_line:
            kv.append(("WINNING_LINE", ",".join(str(i) for i in winning_line)))
        kv.append(("TIMESTAMP", ts))
        msg = self._finalize(kv)
        self.listener.send_unicast(msg, to_ip)
        verbose_log("SEND >", msg)
        return mid
