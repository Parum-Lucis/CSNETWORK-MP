# storage/group_directory.py
from typing import Dict, List

# group_table: { group_id: { "name": str, "members": set(user_id) } }
group_table: Dict[str, Dict] = {}

# group_messages: { group_id: [ { "sender": str, "content": str, "timestamp": str } ] }
group_messages: Dict[str, List[Dict]] = {}


def create_group(group_id: str, group_name: str, members: List[str]):
    """
    Create a group entry with given ID, name, and members.
    Also initializes an empty message list for the group.
    """
    group_table[group_id] = {
        "name": group_name,
        "members": set(members)
    }
    group_messages[group_id] = []  # Initialize empty chat history


def update_group_members(group_id: str, add=None, remove=None):
    """
    Add or remove members from a group.
    """
    if group_id not in group_table:
        return
    if add:
        group_table[group_id]["members"].update(add)
    if remove:
        group_table[group_id]["members"].difference_update(remove)


def get_group_members(group_id: str) -> List[str]:
    """
    Get a list of member IDs for a given group.
    """
    if group_id in group_table:
        return list(group_table[group_id]["members"])
    return []


def get_group_name(group_id: str) -> str:
    """
    Get the display name of a group. Falls back to ID if name not found.
    """
    if group_id in group_table:
        return group_table[group_id]["name"]
    return group_id


def store_group_message(group_id: str, sender: str, content: str, timestamp: str):
    """
    Store a group message for later retrieval.
    Creates message list for group if it doesn't exist yet.
    """
    if group_id not in group_messages:
        group_messages[group_id] = []

    group_messages[group_id].append({
        "sender": sender,
        "content": content,
        "timestamp": timestamp
    })


def get_group_messages(group_id: str) -> List[Dict]:
    """
    Retrieve all stored messages for a group.
    Returns an empty list if no messages are found.
    """
    print("Group Messages: ",group_messages)

    return group_messages.get(group_id, [])
