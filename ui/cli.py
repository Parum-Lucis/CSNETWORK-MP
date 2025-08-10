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
# Queue for storing pending file offers from UDP listener
# This is filled by handle_file() in another thread
# ===============================
pending_file_offers = Queue()

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
                print("The file entered does not exist.")
                continue
            return answers
    except KeyboardInterrupt:
        return None

def process_file_offer(msg, addr, udp):
    """
    Handles a pending file offer from the queue.
    """
    from_user = msg.get("FROM")
    file_name = msg.get("FILENAME")
    file_size = msg.get("FILESIZE")
    ip = addr[0]
    file_id = msg.get("FILEID")

    print(f"\n📥 File offer from {from_user}: {file_name} ({file_size} bytes)")

    accept = questionary.confirm("Accept file?").ask()
    if accept:
        responder = FileTransferResponder(udp)
        responder.accept_file_offer(
            to_ip=ip,
            original_message_id=msg["MESSAGE_ID"]
        )
    else:
        print("❌ File offer declined.")


def launch_main_menu(profile: Profile, udp):
    while True:
        # ✅ Process any pending file offers before showing the menu
        while not pending_file_offers.empty():
            msg, addr = pending_file_offers.get()
            process_file_offer(msg, addr, udp)

        status_note = "(Verbose ON)" if config.VERBOSE else ""

        choice = questionary.select(
            "Select an option:",
            choices=[
                "Post",  # post and broadcast
                "Check Feed",  # read all following posts
                "Peer",  # select an active peer and run actions
                "Group",  # group management
                "Notifications",  # non-verbose logs
                status_note,  # verbose logs
                "Terminate"  # end program
            ]
        ).ask()

        #TODO IMPLEMENT UI
        if choice == "Terminate":
            print("Goodbye.")
            time.sleep(5)
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
                    file_transfer.file_offer()  # triggers offer message

            else:
                continue

        else:
            continue

def select_peer(local_profile):
    """
    Shows a list of available peers and allows user to select one.
    Returns the selected peer object or None.
    """
    try:
        waiting = False
        while True:
            clear_screen()
            print("📡 Live Peer View (auto-refreshes every 3s)")
            peers = get_peers(active_within=300)  # online in last 15 sec
            if not peers:
                if not waiting:
                    waiting = True # waiting flag
                    print("😕 No other peers online. Waiting...") 
                time.sleep(3)
                continue  # keep checking
            
            waiting = False # flags not waiting 
            
            # Format choices from live peers
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
            return selected  # a Profile object
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
                "Send File", # send file transfer offer
                "↩ Return to menu" 
            ]
        ).ask()

        if choice == "↩ Return to menu" or choice is None:
            return None
        return choice
