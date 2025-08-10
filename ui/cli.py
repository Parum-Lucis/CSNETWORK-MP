import sys
import time
import os
import questionary
from queue import Queue

import config
from models.peer import Profile
from utils.base64_utils import encode_image_to_base64
from utils.network_utils import get_local_ip
from storage.peer_directory import get_peers
from utils.printer import clear_screen
from utils.time_utils import wait_for_enter
from models.file_transfer import FileTransfer
from models.file_transfer import FileTransferResponder

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

def launch_main_menu(profile: Profile, udp):
    while True:
        # ✅ Flush background logs
        flush_pending_logs()

        # ✅ Process pending file offers before showing menu
        while not pending_file_offers.empty():
            msg, addr = pending_file_offers.get()
            process_file_offer(msg, addr, udp)

        status_note = "(Verbose ON)" if config.VERBOSE else ""

        choice = questionary.select(
            "Select an option:",
            choices=[
                "Post",
                "Check Feed",
                "Peer",
                "Group",
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
                "Follow",
                "Unfollow",
                "Send File",
                "↩ Return to menu"
            ]
        ).ask()

        if choice == "↩ Return to menu" or choice is None:
            return None
        return choice
