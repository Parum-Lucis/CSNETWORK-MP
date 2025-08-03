import os

from core.udp_broadcast import UDPListener
from core.dispatcher import Dispatcher
from core.profile_broadcast import start_broadcast
from models.peer import Profile
from ui.cli import launch_cli, launch_main_menu
from utils.profile_utils import load_profile_from_file, save_profile_to_file


def main():
    print("LSNP Peer Starting...\n")

    os.makedirs("profiles", exist_ok=True)
    profile_tag = input("Enter a unique profile tag (e.g., denzel1): ").strip()
    filename = f"profiles/{profile_tag}.json"

    if os.path.exists(filename):
        local_profile = load_profile_from_file(filename)
        print(f"Welcome back, {local_profile.display_name}!")
    else:
        local_profile = launch_cli()
        save_profile_to_file(local_profile, filename)

    dispatcher = Dispatcher()
    listener = UDPListener()
    start_broadcast(local_profile, listener)

    try:
        listener.start(dispatcher.handle)
        launch_main_menu(local_profile, listener)
    except KeyboardInterrupt:
        print("Exiting LSNP Peer...")

if __name__ == "__main__":
    main()