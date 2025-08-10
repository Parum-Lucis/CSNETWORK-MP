# storage/group_directory.py
from typing import Dict, List

# group_table: { group_id: { "name": str, "members": set(user_id) } }
group_table: Dict[str, Dict] = {}

def create_group(group_id: str, group_name: str, members: List[str]):
    group_table[group_id] = {
        "name": group_name,
        "members": set(members)
    }

def update_group_members(group_id: str, add=None, remove=None):
    if group_id not in group_table:
        return
    if add:
        group_table[group_id]["members"].update(add)
    if remove:
        group_table[group_id]["members"].difference_update(remove)

def get_group_members(group_id: str) -> List[str]:
    if group_id in group_table:
        return list(group_table[group_id]["members"])
    return []

def get_group_name(group_id: str) -> str:
    if group_id in group_table:
        return group_table[group_id]["name"]
    return group_id