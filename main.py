import os
import questionary
import config
from core.udp_broadcast import UDPListener
from core.dispatcher import Dispatcher
from senders.profile_broadcast import start_broadcast as start_profile_broadcast
from senders.ping_broadcast import start_broadcast as start_ping_broadcast
from ui.cli import launch_cli, launch_main_menu
from utils.printer import clear_screen
from utils.profile_utils import load_profile_from_file, save_profile_to_file

def main():
    print("LSNP Peer Starting...\n")

    # Ask verbose mode on startup
    config.VERBOSE = questionary.confirm("Enable verbose mode?").ask()

    # Profile file handling
    os.makedirs("profiles", exist_ok=True)
    profile_tag = input("Enter a unique profile tag (e.g., denzel1): ").strip()
    filename = f"profiles/{profile_tag}.json"

    if os.path.exists(filename):
        local_profile = load_profile_from_file(filename)
        print(f"Welcome back, {local_profile.display_name}!")
    else:
        local_profile = launch_cli()
        save_profile_to_file(local_profile, filename)

    clear_screen()

    # Network core setup
    dispatcher = Dispatcher()
    listener = UDPListener()

    # Start PROFILE senders loop
    start_profile_broadcast(local_profile, listener)

    # Start PING senders loop (keep-alive)
    start_ping_broadcast(local_profile.user_id, listener)

    # Start UDP listener
    listener.start(dispatcher.handle)

    # CLI main menu
    try:
        launch_main_menu(local_profile, listener)
    except KeyboardInterrupt:
        print("Exiting LSNP Peer...")

if __name__ == "__main__":
    main()