peer_table = {}

def update_peer(user_id, peer_info):
    """
    Adds or updates a peer's profile information in the peer_table

    Args:
        user_id (str): unique identifier of the peer
        peer_info (dict): object with updated profile information
    """
    peer_table[user_id] = peer_info

def get_peers():
    """
    Retrieves a list of all known peer user IDs.

    Returns:
        list[str]: List of user_id strings currently stored in the peer_table.
    """
    return list(peer_table.keys())

def get_peer(user_id):
    """
    Retrieves a list of a certain peer,

    Args:
        user_id (str): the user ID of the peer to retrieve.
    Returns:
        list[str]: the corresponding profile object; else, none
    """
    return peer_table.get(user_id)
