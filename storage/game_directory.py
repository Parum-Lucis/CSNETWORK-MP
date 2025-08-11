"""Thread-safe in-memory store for TicTacToe sessions."""

import threading
import time
from typing import Dict, Optional
from models.game_session import GameSession

_game_table: Dict[str, tuple[GameSession, float]] = {}
_lock = threading.Lock()


def create_session(game: GameSession) -> bool:
    """Add a session. Return False if already exists."""
    with _lock:
        if game.game_id in _game_table:
            return False
        _game_table[game.game_id] = (game, time.time())
        return True


def get_session(game_id: str) -> Optional[GameSession]:
    with _lock:
        entry = _game_table.get(game_id)
        return entry[0] if entry else None


def update_session_last_seen(game_id: str):
    with _lock:
        if game_id in _game_table:
            game, _ = _game_table[game_id]
            _game_table[game_id] = (game, time.time())


def remove_session(game_id: str):
    with _lock:
        if game_id in _game_table:
            del _game_table[game_id]


def list_sessions(active_within: int = 3600):
    now = time.time()
    with _lock:
        return [g for g, ts in _game_table.values() if now - ts <= active_within]


def session_exists(game_id: str) -> bool:
    with _lock:
        return game_id in _game_table
