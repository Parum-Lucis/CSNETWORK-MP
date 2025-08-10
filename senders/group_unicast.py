import time
from storage.peer_directory import get_peer
from storage.group_directory import get_group_members
from utils.token_utils import generate_token

# ====== MESSAGE BUILDERS ====== #
def build_group_create(profile, group_id, group_name, members):
    token = generate_token(profile.user_id, ttl=3600, scope="group")
    return "\n".join([
        "TYPE: GROUP_CREATE",
        f"FROM: {profile.user_id}",
        f"GROUP_ID: {group_id}",
        f"GROUP_NAME: {group_name}",
        f"MEMBERS: {','.join(members)}",
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {token}",
        ""
    ])

def build_group_update(profile, group_id, add=None, remove=None):
    token = generate_token(profile.user_id, ttl=3600, scope="group")
    lines = [
        "TYPE: GROUP_UPDATE",
        f"FROM: {profile.user_id}",
        f"GROUP_ID: {group_id}"
    ]
    if add:
        lines.append(f"ADD: {','.join(add)}")
    if remove:
        lines.append(f"REMOVE: {','.join(remove)}")
    lines.extend([
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {token}",
        ""
    ])
    return "\n".join(lines)

def build_group_message(profile, group_id, content):
    token = generate_token(profile.user_id, ttl=3600, scope="group")
    return "\n".join([
        "TYPE: GROUP_MESSAGE",
        f"FROM: {profile.user_id}",
        f"GROUP_ID: {group_id}",
        f"CONTENT: {content}",
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {token}",
        ""
    ])

# ====== SEND HELPERS ====== #
def send_group_create(profile, group_id, group_name, members, udp_listener):
    """
    Broadcasts GROUP_CREATE to all members.
    """
    message = build_group_create(profile, group_id, group_name, members)
    for member_id in members:
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)

def send_group_update(profile, group_id, udp_listener, add=None, remove=None):
    """
    Sends GROUP_UPDATE to all current group members.
    """
    members = get_group_members(group_id)
    if not members:
        print(f"[ERROR] Group {group_id} not found.")
        return

    message = build_group_update(profile, group_id, add, remove)
    for member_id in members:
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)

def send_group_message(profile, group_id, content, udp_listener):
    """
    Sends GROUP_MESSAGE to all members except the sender.
    """
    members = get_group_members(group_id)
    if not members:
        print(f"[ERROR] Group {group_id} has no members.")
        return

    message = build_group_message(profile, group_id, content)
    for member_id in members:
        if member_id == profile.user_id:
            continue
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)
