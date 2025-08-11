"""TicTacToe game session model (RFC 5.12 - 5.14)."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time


@dataclass
class GameSession:
    """Represents an in-memory TicTacToe session."""
    game_id: str
    player_x: str               # e.g., alice@192.168.1.11
    player_o: str               # e.g., bob@192.168.1.12
    player_x_ip: str
    player_o_ip: str
    # map user_id -> symbol ('X' or 'O')
    symbol_of: Dict[str, str] = field(default_factory=dict)
    board: List[Optional[str]] = field(default_factory=lambda: [None] * 9)
    turn: int = 0               # last applied turn number (0 before 1st)
    status: str = "PENDING"     # PENDING, IN_PROGRESS, COMPLETE, FORFEIT
    winner: Optional[str] = None
    winning_line: Optional[List[int]] = None
    last_update: float = field(default_factory=time.time)
    processed_turns: set = field(default_factory=set)  # processed turns for idempotency

    def assign_symbols(self, inviter_user_id: str, inviter_symbol: str):
        inviter_symbol = (inviter_symbol or "X").upper()
        if inviter_symbol not in ("X", "O"):
            inviter_symbol = "X"
        other_symbol = "O" if inviter_symbol == "X" else "X"
        self.symbol_of[inviter_user_id] = inviter_symbol
        other_user = self.player_o if inviter_user_id == self.player_x else self.player_x
        self.symbol_of[other_user] = other_symbol

    def apply_move(self, user_id: str, position: int, symbol: str, turn_number: int) -> bool:
        """Try to apply a move.

        Returns True if move applied (new), False otherwise (invalid or duplicate).
        Idempotency: if this turn_number was processed, return False (but caller should ACK).
        """
        # idempotency
        if turn_number in self.processed_turns:
            return False

        # basic checks
        if not (0 <= position <= 8):
            return False
        if self.board[position] is not None:
            return False
        expected_symbol = self.symbol_of.get(user_id)
        if expected_symbol != (symbol or "").upper():
            return False
        if turn_number != self.turn + 1:
            return False

        # apply
        self.board[position] = symbol.upper()
        self.turn = turn_number
        self.processed_turns.add(turn_number)
        self.last_update = time.time()
        if self.status == "PENDING":
            self.status = "IN_PROGRESS"
        return True

    def check_winner(self) -> Optional[dict]:
        """Return outcome dict if WIN or DRAW, else None."""
        lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in lines:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                sym = self.board[a]
                # find user_id for symbol
                winner_user = None
                for uid, s in self.symbol_of.items():
                    if s == sym:
                        winner_user = uid
                        break
                return {"result": "WIN", "symbol": sym, "line": [a, b, c], "winner": winner_user}
        # draw
        if all(cell is not None for cell in self.board):
            return {"result": "DRAW"}
        return None

    def other_player(self, user_id: str) -> Optional[str]:
        if user_id == self.player_x:
            return self.player_o
        if user_id == self.player_o:
            return self.player_x
        return None

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "player_x": self.player_x,
            "player_o": self.player_o,
            "board": self.board,
            "turn": self.turn,
            "status": self.status,
            "winner": self.winner,
            "winning_line": self.winning_line
        }
