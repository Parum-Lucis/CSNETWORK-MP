# handlers/group_handler.py

from storage.group_directory import (
    create_group,
    update_group_members,
    get_group_name,
    store_group_message,  # NEW: to log group messages centrally
)
from core.token_validator import validate_token
from utils.printer import NOTIFICATIONS, verbose_log

def handle_group_create(msg, addr):
    """
    Handles a GROUP_CREATE message.
    Validates token, creates group locally, and informs user if they were added.
    """
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_CREATE")
        return

    group_id = msg.get("GROUP_ID")
    group_name = msg.get("GROUP_NAME")
    members = msg.get("MEMBERS", "").split(",")

    create_group(group_id, group_name, members)
    if msg.get("FROM") != members[0]:
        NOTIFICATIONS.append(f"You’ve been added to {group_name}")
    verbose_log(
        "INFO",
        f"Group created: {group_id} ({group_name}) with members {members}"
    )


def handle_group_update(msg, addr):
    """
    Handles a GROUP_UPDATE message.
    Validates token, updates members list, and shows change to user.
    """
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_UPDATE")
        return

    group_id = msg.get("GROUP_ID")
    add = msg.get("ADD", "").split(",") if msg.get("ADD") else None
    remove = msg.get("REMOVE", "").split(",") if msg.get("REMOVE") else None

    update_group_members(group_id, add, remove)
    NOTIFICATIONS.append(f'The group "{get_group_name(group_id)}" member list was updated.')


def handle_group_message(msg, addr):
    """
    Handles a GROUP_MESSAGE message.
    Validates token, stores message in group directory, and prints to console.
    """
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_MESSAGE")
        return

    group_id = msg.get("GROUP_ID")
    sender = msg.get("FROM")
    content = msg.get("CONTENT")
    timestamp = msg.get("TIMESTAMP")

    # Store in group_directory for later retrieval by CLI
    store_group_message(group_id, sender, content, timestamp)

    # Live print for active session
    NOTIFICATIONS.append(f"[{get_group_name(group_id)}] {sender}: {content}")
