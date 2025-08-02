from core.udp_broadcast import UDPListener
from core.dispatcher import Dispatcher
from core.profile_broadcast import start_broadcast
from models.peer import Profile
from ui.cli import launch_cli

def main():
    print("LSNP Peer Starting...")

    #TODO CLI

    # Temp Profile without INPUT
    local_profile = Profile(
        user_id="denzel@192.168.1.5",
        ip="192.168.1.5",
        display_name="Denzel",
        status="Working on LSNP",
        avatar_type=None,
        avatar_data=None
    )

    #TODO DISPATCHER
    dispatcher = Dispatcher()
    #TODO UDP LISTENER
    listener = UDPListener()
    #TODO PROFILE BROADCAST
    start_broadcast(local_profile, listener)

    try:
        listener.start(dispatcher.handle)
    except KeyboardInterrupt:
        print("Exiting LSNP Peer...")

if __name__ == "__main__":
    main()