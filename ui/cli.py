import sys
import time
import os
import uuid

import questionary
from queue import Queue

import config
from models.peer import Profile
from senders.group_unicast import build_group_update, build_group_create, build_group_message, send_group_message
from senders.revoke_sender import send_revoke
from storage.group_directory import create_group, get_group_messages, group_table, get_group_members, get_group_name, update_group_members
from utils.base64_utils import encode_image_to_base64
from utils.network_utils import get_local_ip
from storage.peer_directory import get_peers
from utils.printer import clear_screen, VERBOSE_LOGS, NOTIFICATIONS
from utils.time_utils import wait_for_enter
from models.file_transfer import FileTransfer
from models.file_transfer import FileTransferResponder
from storage.post_store import get_recent_posts
from storage.likes_store import get_like_count, has_liked, add_like, remove_like
from senders.like_unlike import send_like
from storage.dm_store import get_thread
from storage.peer_directory import get_peer
from senders.post_broadcast import send_post
from senders.direct_message_unicast import send_dm
from storage.group_directory import get_group_messages
from senders.group_unicast import send_group_message
from senders.follow_unicast import follow_user, unfollow_user
from storage.user_followers import is_following, is_follower, get_followers, get_following


# ===============================
# Queues shared with background handlers
# ===============================
pending_file_offers = Queue()  # For file offers requiring user action
pending_logs = Queue()         # For async logs (ACKs, file saved, warnings, etc.)

def launch_cli() -> Profile:
    """
    CLI prompt to create a new profile.
    """
    print("No saved profile found. Let's create one!\n")

    display_name = questionary.text("Enter your display name:").ask()
    user_id = f"{display_name.lower()}@{get_local_ip()}"

    avatar_type = None
    avatar_data = None

    use_avatar = questionary.confirm("Would you like to add an avatar?").ask()
    if use_avatar:
        avatar_path = questionary.path("Enter path to image file (PNG, JPG under 10KB):").ask()
        result = encode_image_to_base64(avatar_path)
        if result:
            avatar_type, avatar_data = result
        else:
            print("Failed to load avatar. Proceeding without it.")

    return Profile(
        user_id=user_id,
        ip=get_local_ip(),
        display_name=display_name,
        status="Online",
        avatar_type=avatar_type,
        avatar_data=avatar_data
    )

def file_form():
    """
    Prompts user for file location, name override, and description.
    """
    answers = {}
    try:
        while True:
            file_loc = questionary.text("Enter the file location:").ask()

            if file_loc:    
                if os.path.isfile(file_loc):
                    answers["file_location"] = file_loc
                    answers["file_name"] = questionary.text("Enter the file name to use (empty to use the default):").ask()
                    answers["description"] = questionary.text("Enter the file description:").ask()
                else:
                    questionary.print("❌ The file entered does not exist.", style="bold fg:red")
                    continue
            return answers
    except KeyboardInterrupt:
        return None

def flush_pending_logs():
    """Flush any logs from the pending_logs queue to the terminal immediately."""
    while not pending_logs.empty():
        log = pending_logs.get()
        questionary.print(log, style="fg:yellow")

def process_file_offer(msg, addr, udp, local_profile):
    """
    Handles a pending file offer from the queue.
    """
    from_user_id = msg.get("FROM")
    to_user_id = msg.get("TO")
    file_name = msg.get("FILENAME")
    file_size = msg.get("FILESIZE")
    sender_ip = addr[0]

    print(f"\n📥 User {from_user_id} is sending you a file. "
          f"Do you accept? {file_name} ({file_size} bytes)")

    clear_screen()
    questionary.print(f"\n📥 User {from_user_id} is sending you a file do you accept? {file_name} ({file_size} bytes)")
    accept = questionary.confirm("Accept file?").ask()
    if accept:
        from models.file_transfer import FileTransferResponder
        responder = FileTransferResponder(udp)
        responder.accept_file_offer(
            to_ip=sender_ip,
            file_id=msg["FILEID"]
        )
    else:
        questionary.print("❌ File offer declined.")
        # Receiver sends REVOKE to sender
        send_revoke(
            udp_listener=udp,
            from_profile=local_profile,    # Must be the full profile object
            token=msg.get("TOKEN"),
            target_ip=sender_ip
        )

    # Flush any logs that may have appeared during this process
    flush_pending_logs()

def find_peer_by_user_id(user_id: str):
    peers = get_peers(active_within=300)
    for p in peers:
        if getattr(p, "user_id", None) == user_id:
            return p
    return None

def display_dm_thread(profile, peer_id: str, udp):
    thread = get_thread(peer_id, profile.user_id, limit=50)
    if not thread:
        questionary.print("No messages in this thread yet.", style="fg:yellow")
        wait_for_enter()
        clear_screen()
        return
    
    questionary.print(f"💬 Conversation with {peer_id}\n", style="bold")
    for msg in thread:
        timestamp = msg.get("TIMESTAMP")
        who = "You" if msg.get("FROM") == profile.user_id else peer_id
        questionary.print(f"[{timestamp}] {who}: {msg.get('CONTENT')}")

    action = questionary.select(
            "Choose an action:",
            choices=["Reply", "↩ Back"]
    ).ask()

    if action == "Reply":
        peer = find_peer_by_user_id(peer_id)
        if not peer:
            questionary.print("⚠️ Peer is not currently online; cannot send.", style="fg:yellow")
            wait_for_enter()
            return
        reply = questionary.text("Type your reply:").ask()
        if reply and reply.strip():
            send_dm(profile, peer, reply, udp)
            questionary.print("📤 Sent.", style="fg:green")
            wait_for_enter()

    clear_screen()

def group_menu(local_profile, udp_listener):
    """
    Main Group Menu
    """
    while True:
        choice = questionary.select(
            "Group Menu:",
            choices=[
                "Create Group",
                "Update Group",
                "View My Groups",
                "Send Message to Group",
                "View Messages in Group",
                "↩ Return to menu"
            ]
        ).ask()

        if choice == "Create Group":
            create_group_cli(local_profile, udp_listener)
        
        elif choice == "Update Group":
            update_group_cli(local_profile, udp_listener)
        
        elif choice == "View My Groups":
            view_groups_cli()

        elif choice == "Send Message to Group":
            send_group_message_cli(local_profile, udp_listener)

        elif choice == "View Messages in Group":
            view_group_messages_cli()

        elif choice == "↩ Return to menu":
            break

def create_group_cli(local_profile, udp_listener):
    # Generate random group ID
    group_id = f"group_{uuid.uuid4().hex[:8]}"

    # Ask for group name
    group_name = questionary.text("Enter a group name:").ask()

    # Get active peers (excluding yourself)
    peers = [p for p in get_peers(active_within=300) if p.user_id != local_profile.user_id]

    if not peers:
        questionary.print("⚠ No active peers to add right now.")
        return

    # Let user select peers to add
    selected_users = questionary.checkbox(
        "Select members to add:",
        choices=[f"{p.display_name} ({p.user_id})" for p in peers]
    ).ask()

    # Map selection back to user IDs
    selected_ids = [p.user_id for p in peers if f"{p.display_name} ({p.user_id})" in selected_users]

    # Always include yourself
    if local_profile.user_id not in selected_ids:
        selected_ids.append(local_profile.user_id)

    # Create group locally
    create_group(group_id, group_name, selected_ids)

    # Broadcast GROUP_CREATE
    msg = build_group_create(local_profile, group_id, group_name, selected_ids)
    udp_listener.send_broadcast(msg)

    questionary.print(f"✅ Group '{group_name}' created with members: {', '.join(selected_ids)}")

def view_groups_cli():
    if not group_table:
        questionary.print("No groups found.")
        return

    for gid, data in group_table.items():
        questionary.print(f"\n📌 {data['name']} ({gid})")
        questionary.print("Members:")
        for member in sorted(data["members"]):
            questionary.print(f" - {member}")

def update_group_cli(local_profile, udp_listener):
    # Get list of existing groups
    groups = [(gid, get_group_name(gid)) for gid in group_table.keys()]

    if not groups:
        questionary.print("⚠ No existing groups to update.")
        return

    # Select which group to update
    group_choice = questionary.select(
        "Select a group to update:",
        choices=[f"{name} ({gid})" for gid, name in groups]
    ).ask()
    if not group_choice:
        questionary.print("❌ No group selected.")
        return

    selected_group_id = next(gid for gid, name in groups if f"{name} ({gid})" == group_choice)
    selected_group_name = get_group_name(selected_group_id)

    # Current members
    current_members = get_group_members(selected_group_id)

    # Active peers (excluding yourself)
    peers = [p for p in get_peers(active_within=300) if p.user_id != local_profile.user_id]

    # ADD
    add_ids = []
    add_choices = [f"{p.display_name} ({p.user_id})" for p in peers if p.user_id not in current_members]
    if add_choices:
        add_selection = questionary.checkbox("Select members to ADD:", choices=add_choices).ask() or []
        add_ids = [p.user_id for p in peers if f"{p.display_name} ({p.user_id})" in add_selection]
    else:
        questionary.print("ℹ No members available to add.")

    # REMOVE
    remove_ids = []
    remove_choices = [uid for uid in current_members if uid != local_profile.user_id]
    if remove_choices:
        remove_selection = questionary.checkbox("Select members to REMOVE:", choices=remove_choices).ask() or []
        remove_ids = [uid for uid in current_members if uid in remove_selection]
    else:
        questionary.print("ℹ No members available to remove.")

    # No changes?
    if not add_ids and not remove_ids:
        questionary.print("⚠ No changes selected.")
        return

    # Local update
    update_group_members(selected_group_id, add=add_ids, remove=remove_ids)

    # Broadcast
    update_msg = build_group_update(
        local_profile,
        selected_group_id,
        add_ids if add_ids else None,
        remove_ids if remove_ids else None
    )
    udp_listener.send_broadcast(update_msg)

    NOTIFICATIONS.append(f"✅ Group '{selected_group_name}' updated.")

def send_group_message_cli(local_profile, udp_listener):
    """
    Prompts the user to select a group and send a message to its members.
    """
    if not group_table:
        print("No groups to send messages to.")
        return

    # Choose a group, keeping the group_id as the actual value
    groups = [(gid, get_group_name(gid)) for gid in group_table.keys()]
    gid = questionary.select(
        "Select a group:",
        choices=[questionary.Choice(title=f"{name} ({gid})", value=gid) for gid, name in groups]
    ).ask()

    if not gid:
        print("❌ No group selected.")
        return

    content = questionary.text("Enter your message:").ask()

    # Import here to avoid circulars

    send = send_group_message(local_profile, gid, content, udp_listener)
    if send:
        NOTIFICATIONS.append(f"📤 Message sent to group '{get_group_name(gid)}'.")
    
def view_group_messages_cli():
    """
    Allows the user to view stored messages for a group.
    """

    if not group_table:
        print("No groups available.")
        return

    groups = [(gid, get_group_name(gid)) for gid in group_table.keys()]
    gid = questionary.select(
        "Select a group:",
        choices=[questionary.Choice(title=f"{name} ({gid})", value=gid) for gid, name in groups]
    ).ask()

    if not gid:
        print("❌ No group selected.")
        return

    messages = get_group_messages(gid)
    if not messages:
        print("📭 No messages in this group yet.")
    else:
        questionary.print(f"=== Messages in '{get_group_name(gid)}' ===")
        for m in messages:
            questionary.print(f"[{m['timestamp']}] {m['sender']}: {m['content']}")

    input("\n🔙 Press Enter to return to the main menu...")


def launch_main_menu(profile: Profile, udp):
    while True:

        questionary.print(f"User: {profile.user_id}", style="bold fg:yellow")

        # ✅ Flush background logs
        flush_pending_logs()


        # ✅ Process pending file offers before showing menu
        while not pending_file_offers.empty():
            msg, addr = pending_file_offers.get()
            process_file_offer(msg, addr, udp, profile)

        console = "(Verbose ON)" if config.VERBOSE else ""

        if config.VERBOSE:
            choice = questionary.select(
                "Select an option:",
                choices=[
                    "Post",
                    "Check Feed",
                    "Peer",
                    "Groups",
                    "Notifications",
                    "Verbose Console",
                    "Settings: Change Post TTL",
                    "Revoke Token",
                    "Refresh",
                    "Terminate"
                ]
            ).ask()

        else:
            choice = questionary.select(
                "Select an option:",
                choices=[
                    "Post",
                    "Check Feed",
                    "Peer",
                    "Groups",
                    "Notifications",
                    "Settings: Change Post TTL",
                    "Refresh",
                    "Terminate"
                ]
            ).ask()

        if choice == "Terminate":
            questionary.print("👋 Goodbye.", style="bold fg:green")
            time.sleep(1)
            sys.exit(0)

        elif choice == "Peer":
            selected = select_peer(profile)
            if selected:
                choice = peer_menu()

                if choice == "Send File":
                    clear_screen()
                    file_result = file_form()
                    file_transfer = FileTransfer(
                        profile,
                        selected,
                        file_result["file_location"],
                        file_result["description"],
                        udp,
                        file_result["file_name"]
                    )
                    file_transfer.file_offer()

                elif choice == "DM":
                    content = questionary.text("Enter your message:").ask()
                    send_dm(profile, selected, content, udp)

                elif choice == "DM Thread":
                    display_dm_thread(profile, selected.user_id, udp)
                
                elif choice == "Follow":
                    if is_following(selected.user_id):
                        questionary.print("✅ You already follow this user.", style="fg:green")
                    else:
                        follow_user(profile, selected, udp)

                elif choice == "Unfollow":
                    if not is_following(selected.user_id):
                        questionary.print("ℹ️ You don't follow this user.", style="fg:yellow")
                    else:
                        unfollow_user(profile, selected, udp)

                elif choice == "View Relationship":
                    show_peer_relationship(selected)

        elif choice == "Settings: Change Post TTL":
            new_post_ttl = questionary.text(f"Enter new Post TTL in seconds (current {config.token_ttl_post}): ").ask()

            try:
                config.token_ttl_post = int(new_post_ttl)
                questionary.print(f"✅ Post TTL updated to {new_post_ttl} seconds.", style="fg:green")
            except ValueError:
                questionary.print(f"❌ Invalid number. TTL not changed.", style="fg=red")

        elif choice == "Post":
            content = questionary.text("Enter your post content:").ask()
            send_post(profile, content, udp)

        elif choice == "Check Feed":
            display_feed(profile, udp)

        elif choice == "Groups":
            group_menu(profile, udp)

        elif choice == "Verbose Console":
            print_verbose()

        elif choice == "Revoke Token":
            revoke_cli(profile, udp)

        elif choice == "Notifications":
            print_notifs()
        elif choice == "Refresh":
            continue
        else:
            continue

def select_peer(local_profile):
    """
    Shows a list of available peers and allows user to select one.
    """
    try:
        waiting = False
        while True:
            clear_screen()
            questionary.print("📡 Live Peer View (auto-refreshes every 3s)", style="bold")
            peers = get_peers(active_within=300)
            peers = [p for p in peers if local_profile.user_id != p.user_id]

            if not peers:
                if not waiting:
                    waiting = True
                    questionary.print("😕 No other peers online. Waiting...", style="fg:yellow")
                time.sleep(3)
                continue

            waiting = False
            choices = [
                questionary.Choice(
                    title=f"{peer.display_name} ({peer.status}) @ {peer.ip}",
                    value=peer
                ) for peer in peers
            ]
            choices.append("↩ Return to menu")

            selected = questionary.select(
                "📡 Choose a peer to connect:",
                choices=choices
            ).ask()

            if selected == "↩ Return to menu" or selected is None:
                return None
            return selected
    except KeyboardInterrupt:
        return None

def peer_menu():
    """
    Menu for selecting operations for a specific peer.
    """
    while True:
        choice = questionary.select(
            "Select an operation to run:",
            choices=[
                "DM",
                "DM Thread",
                "Follow",
                "Unfollow",
                "View Relationship",
                "Send File",
                "↩ Return to menu"
            ]
        ).ask()

        if choice == "↩ Return to menu" or choice is None:
            return None
        return choice
    
def display_feed(profile=None, udp=None):
    posts = get_recent_posts()
    if not posts:
        questionary.print("📭 No posts to show.", style="fg:yellow")
        wait_for_enter()
        return
    
    choices = []
    for post in posts:
        user_id = post.get("USER_ID", "?")
        timestamp  = int(post.get("TIMESTAMP", 0))
        content = (post.get("CONTENT") or "").strip().replace("\n", " ")
        if len(content) > 70:
            content = content[:67] + "..."
        count = get_like_count(user_id, timestamp)
        title = f"{user_id} • {timestamp}\n   {content}  ❤️ {count}"
        choices.append(questionary.Choice(title=title, value=post))

    choices.append("↩ Back")

    selected = questionary.select("📰 Feed — pick a post:", choices=choices).ask()
    if selected == "↩ Back" or selected is None:
        return
    
    post_author = selected.get("USER_ID")
    post_ts = int(selected.get("TIMESTAMP", 0))
    
    action = questionary.select("Choose an action:", choices=["Like", "Unlike", "↩ Back"]).ask()
    if action in ("Like", "Unlike"):
        if profile is None or udp is None:
            questionary.print("⚠️ Internal: missing profile/udp in display_feed.", style="fg:red")
            wait_for_enter()
            return
        
        if action == "Like":
            if has_liked(post_author, post_ts, profile.user_id):
                questionary.print("✅ You already liked this post.", style="fg:green")
            else:
                add_like(post_author, post_ts, profile.user_id)
                from senders.like_unlike import send_like
                send_like(profile, selected, udp, action="LIKE")
                questionary.print("❤️ Liked.", style="fg:green")

        elif action == "Unlike":
            if not has_liked(post_author, post_ts, profile.user_id):
                questionary.print("ℹ️ You haven’t liked this post yet.", style="fg:yellow")
            else:
                remove_like(post_author, post_ts, profile.user_id)
                from senders.like_unlike import send_like
                send_like(profile, selected, udp, action="UNLIKE")
                questionary.print("💤 Unliked.", style="fg:green")

        wait_for_enter()

def revoke_cli(local_profile, udp_listener):
    """
    CLI function to manually revoke a token.

    Args:
        local_profile: Profile of the local user.
        udp_listener: UDP listener instance for sending messages.
    """
    token = questionary.text("Enter token to revoke:").ask()
    if not token:
        print("❌ No token entered.")
        return

    revoke = send_revoke(udp_listener, local_profile, token)
    if revoke:
        print(f"✅ Token revoked: {token}")
    else:
        print(f"❌ Cannot token: {token}")

def print_verbose():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== Verbose Logs ===\n")
        for log in VERBOSE_LOGS:
            print(log)
        print("\nRefreshing in 10 seconds... Press Ctrl+C to return.")

        try:
            time.sleep(10)
            clear_screen()
            continue
        except KeyboardInterrupt:
            # Return to menu when Ctrl+C is pressed
            clear_screen()
            break

        time.sleep(10)

def print_notifs():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== Notifications ===\n")
        for log in NOTIFICATIONS:
            print(log)
        print("\nRefreshing in 10 seconds... Press Ctrl+C to return.")

        try:
            time.sleep(10)
            clear_screen()
        except KeyboardInterrupt:
            # Return to menu when Ctrl+C is pressed
            clear_screen()
            break

        time.sleep(10)

def show_peer_relationship(peer):
    you_follow = is_following(peer.user_id)
    they_follow = is_follower(peer.user_id)

    lines = [
        f"👤 Peer: {peer.user_id}",
        f"• You follow them: {'✅ Yes' if you_follow else '❌ No'}",
        f"• They follow you: {'✅ Yes' if they_follow else '❌ No'}",
    ]
    questionary.print("\n".join(lines), style="bold")
    wait_for_enter()
