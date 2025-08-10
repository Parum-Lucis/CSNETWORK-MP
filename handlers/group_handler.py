from storage.group_directory import create_group, update_group_members, get_group_name
from core.token_validator import validate_token
from utils.printer import verbose_log

def handle_group_create(msg, addr):
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_CREATE")
        return

    group_id = msg.get("GROUP_ID")
    group_name = msg.get("GROUP_NAME")
    members = msg.get("MEMBERS", "").split(",")

    create_group(group_id, group_name, members)
    if msg.get("FROM") != members[0]:
        print(f"You’ve been added to {group_name}")
    verbose_log("INFO", f"Group created: {group_id} ({group_name}) with members {members}")

def handle_group_update(msg, addr):
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_UPDATE")
        return

    group_id = msg.get("GROUP_ID")
    add = msg.get("ADD", "").split(",") if msg.get("ADD") else None
    remove = msg.get("REMOVE", "").split(",") if msg.get("REMOVE") else None

    update_group_members(group_id, add, remove)
    print(f'The group "{get_group_name(group_id)}" member list was updated.')

def handle_group_message(msg, addr):
    if not validate_token(msg.get("TOKEN"), "group"):
        verbose_log("DROP!", "Invalid token for GROUP_MESSAGE")
        return

    sender = msg.get("FROM")
    content = msg.get("CONTENT")
    print(f'{sender} sent "{content}"')