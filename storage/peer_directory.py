from time import time
from typing import Dict
from models.peer import Profile

peer_table: Dict[str, tuple[Profile, float]] = {}

def update_peer(user_id: str, profile: Profile):
    """
    Adds or updates a peer's Profile in the in-memory peer table.

    Args:
        user_id (str): The peer's unique identifier
        profile (Profile): The peer's profile data.
    """
    peer_table[user_id] = (profile, time())

def get_peers(active_within=300):
    """
    Looks up and returns all known peer Profile objects.

    Returns:
        list[Profile]: A list of all known peer Profile objects.
    """
    now = time()
    return [
        profile
        for profile, last_seen in peer_table.values()
        if now - last_seen <= active_within
    ]

def get_peer(user_id: str) -> Profile | None:
    """
    Looks up and returns a specific peer's Profile.

    Args:
        user_id (str): The peer's unique identifier.

    Returns:
        Profile | None: The profile if found; else, none.
    """
    entry = peer_table.get(user_id)
    return entry[0] if entry else None