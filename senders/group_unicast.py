import time
from storage.peer_directory import get_peer
from storage.group_directory import get_group_members
from utils.token_utils import generate_token
from utils.printer import verbose_log
from storage.group_directory import store_group_message  # add this import


def build_group_create(profile, group_id, group_name, members):
    ttl = int(time.time()) + 600  # Fixed 600s TTL
    return "\n".join([
        "TYPE: GROUP_CREATE",
        f"FROM: {profile.user_id}",
        f"GROUP_ID: {group_id}",
        f"GROUP_NAME: {group_name}",
        f"MEMBERS: {','.join(members)}",
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {generate_token(profile.user_id, ttl, scope='group')}",
        ""
    ])


def build_group_update(profile, group_id, add=None, remove=None):
    ttl = int(time.time()) + 600  # Fixed 600s TTL
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
        f"TOKEN: {generate_token(profile.user_id, ttl, scope='group')}",
        ""
    ])
    return "\n".join(lines)


def build_group_message(profile, group_id, content):
    ttl = int(time.time()) + 600  # Fixed 600s TTL
    return "\n".join([
        "TYPE: GROUP_MESSAGE",
        f"FROM: {profile.user_id}",
        f"GROUP_ID: {group_id}",
        f"CONTENT: {content}",
        f"TIMESTAMP: {int(time.time())}",
        f"TOKEN: {generate_token(profile.user_id, ttl, scope='group')}",
        ""
    ])


def send_group_create(profile, group_id, group_name, members, udp_listener):
    """
    Sends GROUP_CREATE to all specified members.
    """
    message = build_group_create(profile, group_id, group_name, members)
    for member_id in members:
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)
            verbose_log("INFO", f"GROUP_CREATE sent to {member_id}")
        else:
            verbose_log("WARN", f"Member {member_id} is offline; skipping send.")


def send_group_update(profile, group_id, udp_listener, add=None, remove=None):
    """
    Sends GROUP_UPDATE to all current group members.
    """
    members = get_group_members(group_id)
    if not members:
        print(f"⚠️ [ERROR] Group {group_id} not found.")
        return

    message = build_group_update(profile, group_id, add, remove)
    for member_id in members:
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)
            verbose_log("INFO", f"GROUP_UPDATE sent to {member_id}")
        else:
            verbose_log("WARN", f"Member {member_id} is offline; skipping send.")


def send_group_message(profile, group_id, content, udp_listener):
    """
    Sends GROUP_MESSAGE to all members except the sender.
    Stores the message locally so the sender can see it too.
    """
    members = get_group_members(group_id)
    if not members:
        print(f"⚠️ [ERROR] Group {group_id} has no members.")
        return False

    timestamp = int(time.time())
    message = build_group_message(profile, group_id, content)

    # Store locally for the sender
    store_group_message(group_id, profile.user_id, content, timestamp)

    for member_id in members:
        if member_id == profile.user_id:
            continue  # skip self
        peer = get_peer(member_id)
        if peer:
            udp_listener.send_unicast(message, peer.ip)
            verbose_log("INFO", f"GROUP_MESSAGE sent to {member_id}")
        else:
            verbose_log("WARN", f"Member {member_id} is offline; skipping send.")
    return True
