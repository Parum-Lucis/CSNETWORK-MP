import sys
import time
import os
import uuid

import questionary
from queue import Queue

import config
from models.peer import Profile
from senders.group_unicast import build_group_update, build_group_create, build_group_message
from storage.group_directory import create_group, group_table, get_group_members, get_group_name
from utils.base64_utils import encode_image_to_base64
from utils.network_utils import get_local_ip
from storage.peer_directory import get_peers
from utils.printer import clear_screen, VERBOSE_LOGS, NOTIFICATIONS
from utils.time_utils import wait_for_enter
from models.file_transfer import FileTransfer
from models.file_transfer import FileTransferResponder
from storage.post_store import get_recent_posts
from storage.dm_store import get_thread
from storage.peer_directory import get_peer
from senders.post_broadcast import send_post
from senders.direct_message_unicast import send_dm


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
            file_loc = questionary.text("Enter the file location").ask()

            if os.path.isfile(file_loc):
                answers["file_location"] = file_loc
                answers["file_name"] = questionary.text("Enter the file name to use (empty to use the default)").ask()
                answers["description"] = questionary.text("Enter the file description: ").ask()
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

def process_file_offer(msg, addr, udp):
    """
    Handles a pending file offer from the queue.
    """
    from_user = msg.get("FROM")
    file_name = msg.get("FILENAME")
    file_size = msg.get("FILESIZE")
    ip = addr[0]

    print(f"\n📥 User {from_user} is sending you a file do you accept? {file_name} ({file_size} bytes)")
    accept = questionary.confirm("Accept file?").ask()
    if accept:
        from models.file_transfer import FileTransferResponder
        responder = FileTransferResponder(udp)
        responder.accept_file_offer(
            to_ip=ip,
            file_id=msg["FILEID"]
        )
    else:
        print("❌ File offer declined.")

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
                "View My Groups",
                "Send Message to Group",
                "Back to Main Menu"
            ]
        ).ask()

        if choice == "Create Group":
            create_group_cli(local_profile, udp_listener)

        elif choice == "View My Groups":
            view_groups_cli()

        elif choice == "Send Message to Group":
            send_group_message_cli(local_profile, udp_listener)

        elif choice == "Back to Main Menu":
            break

def create_group_cli(local_profile, udp_listener):
    # Generate random group ID
    group_id = f"group_{uuid.uuid4().hex[:8]}"

    # Ask for group name
    group_name = questionary.text("Enter a group name:").ask()

    # Get active peers (excluding yourself)
    peers = [p for p in get_peers(active_within=300) if p.user_id != local_profile.user_id]

    if not peers:
        print("⚠ No active peers to add right now.")
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

    print(f"✅ Group '{group_name}' created with members: {', '.join(selected_ids)}")

def view_groups_cli():
    if not group_table:
        print("No groups found.")
        return

    for gid, data in group_table.items():
        print(f"\n📌 {data['name']} ({gid})")
        print("Members:")
        for member in sorted(data["members"]):
            print(f" - {member}")


def send_group_message_cli(local_profile, udp_listener):
    if not group_table:
        print("No groups to send messages to.")
        return

    # Choose a group
    gid = questionary.select(
        "Select a group:",
        choices=[gid for gid in group_table.keys()]
    ).ask()

    content = questionary.text("Enter your message:").ask()

    msg = build_group_message(local_profile, gid, content)

    # Send to each group member except self
    for member in get_group_members(gid):
        if member != local_profile.user_id:
            member_ip = member.split("@")[1]
            udp_listener.send_unicast(msg, member_ip)

    print(f"📤 Message sent to group '{get_group_name(gid)}'.")



def launch_main_menu(profile: Profile, udp):
    while True:
        # ✅ Flush background logs
        flush_pending_logs()

        # ✅ Process pending file offers before showing menu
        while not pending_file_offers.empty():
            msg, addr = pending_file_offers.get()
            process_file_offer(msg, addr, udp)

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
            display_feed()

        elif choice == "Groups":
            group_menu(profile, udp)

        elif choice == "Verbose Console":
            print_verbose()

        elif choice == "Notifications":
            print_notifs()

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
                "Send File",
                "↩ Return to menu"
            ]
        ).ask()

        if choice == "↩ Return to menu" or choice is None:
            return None
        return choice
    
def display_feed():
    posts = get_recent_posts()
    if not posts:
        questionary.print("📭 No posts to show.", style="fg:yellow")
        wait_for_enter()
        return

    for post in posts:
        questionary.print(f"📭 Post from {post.get('USER_ID')}: {post.get('CONTENT')}")
    wait_for_enter()

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
