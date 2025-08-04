import sys
import time

import questionary

import config
from models.peer import Profile
from utils.base64_utils import encode_image_to_base64
from utils.network_utils import get_local_ip
from storage.peer_directory import get_peers
from utils.printer import clear_screen
from utils.time_utils import wait_for_enter
import os
from handlers.file_handler import handle_file_transfer

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

def launch_main_menu(profile: Profile, udp):
    while True:
        status_note = "(Verbose ON)" if config.VERBOSE else ""

        choice = questionary.select(
            "Select an option:",
            choices=[
                "Post", # post and broadcast
                "Check Feed", # read all following posts with like or dislike. move from different post to like and dislike using arrow keys
                "Peer", # this is where you select an active peer using arrow keys and select an action using numbers to do DM, FTP, Game
                "Group", # Group Create, Update, and Message
                "Notifications", # put non-verbose logs
                status_note, # put verbose logs
                "Terminate" #end
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
                choice = peer_menu(selected)          
            else:
                continue
        else:
            continue
        """
        if choice == "Post":
            # post_menu(profile, udp)
        elif choice == "Feed":
            # feed_menu()
        elif choice == "Peer":
            #peer_menu(profile, udp)
        elif choice == "Notifications":
            #show_notifications()
        elif choice == "Verbose Logs":
            #toggle_verbose()
        elif choice == "Terminate":
            #print("Goodbye.")
            break
        """

# def show_peers(local_profile):
#     try:
#         while True:
#             clear_screen()
#             print("📡 Live Peer View (auto-refreshes every 3s)")
#             peers = get_peers(active_within=300)  # online in last 15 sec
#             if not peers:
#                 print("No peers online yet.")
#             else:
#                 for peer in peers:
#                     if peer.user_id == local_profile.user_id:
#                         continue
#                     print(f" - {peer.display_name} @ {peer.ip}")
#                     if peer.status:
#                         print(f"     Status: {peer.status}")
#                     if peer.avatar_type:
#                         print(f"     Avatar Type: {peer.avatar_type}")
#             print("\nPress Ctrl+C to return to menu.")
#             time.sleep(3)
#     except KeyboardInterrupt:
#         clear_screen()
#         return


def select_peer(local_profile):
    """
    Shows a list of available peers and allows user to select one.
    Returns the selected peer object or None.
    """
    try:
        waiting = False
        while True:
            peers = get_peers(active_within=300)
            peers = [p for p in peers if p.user_id != local_profile.user_id]

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

def peer_menu(to_profile):
    while True:
        choice = questionary.select(
            "Select an operation to run:",
            choices=[
                "DM", 
                "Follow",
                "Unfollow",
                "Send File", # TODO implement functionality
                "↩ Return to menu" 
            ]
        ).ask()

        if choice == "Send File":
            handle_file_transfer()
        else:
            continue

        if choice == "↩ Return to menu" or choice is None:
            return None
        # return choice 
        