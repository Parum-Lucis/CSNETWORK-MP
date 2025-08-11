Two Twins LSNP is an LSNP python implementation with richer client-side features to handle, send, and preprocess protocol messages much more user-friendly while still adhering to protocol standards. With greater liberty taken at when messages are shown, Two Twins LSNP creates a dynamic social networking environment that drops raw messaging of input and output to take a more intuitive interface.

## Prerequisites/Dependencies
1. Python 3.13 or latest
2. Python Libraries (via python library manager i.e. pip)
	click
	rich
	pytest
	loguru
	Pillow
	questionary

project/
└── src/
    ├── main.py                  # Entry point; initializes and starts the application.
    ├── config.py                # Centralized config (constants, env vars, settings).

    ├── core/                    # Core system logic modules
    │   ├── ack_registry.py       # Tracks message acknowledgments
    │   ├── dispatcher.py         # Routes incoming messages to handlers
    │   ├── token_validator.py    # Validates security/auth tokens
    │   ├── udp_broadcast.py      # Sends UDP broadcast messages
    │   └── udp_singleton.py      # Singleton UDP listener management

    ├── handlers/                # Message-specific handler modules
    │   ├── ack_handler.py
    │   ├── direct_message_handler.py
    │   ├── file_handler.py
    │   ├── game_handler.py
    │   ├── group_handler.py
    │   ├── ping_handler.py
    │   ├── post_handler.py
    │   ├── profile_handler.py
    │   ├── like_handler.py
    │   ├── revoke_handler.py
    │   └── user_followers_handler.py

    ├── senders/                 # Modules for sending specific data/messages
    │   ├── direct_message_unicast.py
    │   ├── game_invite_unicast.py
    │   ├── group_unicast.py
    │   ├── ping_broadcast.py
    │   ├── post_broadcast.py
    │   ├── profile_broadcast.py
    │   ├── follow_unicast.py
    │   ├── like_unlike.py
    │   └── revoke_sender.py

    ├── models/                  # Data models and domain objects
    │   ├── file_transfer.py
    │   ├── game_session.py
    │   ├── group.py
    │   ├── message.py
    │   └── peer.py

    ├── storage/                 # Local data persistence and caches
    │   ├── dm_store.py
    │   ├── group_directory.py
    │   ├── message_store.py
    │   ├── peer_directory.py
    │   ├── post_store.py
    │   ├── revocation_list.py
    │   ├── user_followers.py
    │   └── likes_store.py

    ├── ui/                      # User interfaces
    │   └── cli.py               # Command-line interface module

    └── utils/                   # Helper utilities and functions
        ├── base64_utils.py
        ├── message_builder.py
        ├── network_utils.py
        ├── printer.py
        ├── profile_utils.py
        ├── time_utils.py
        └── token_utils.py

	

## Running the Project
To install dependencies, run pip install -r requirements.txt
In terminal in the project directory, call python main.py

Enter a username and set verbose mode on/off

## CLI Commands

Once inside the main menu, you can traverse via arrow keys/WASD and enter to interact with the user interface:

### Macro-Social Features
- POST (broadcast post to all followers)
- CHECK FEED (read posts of following & group?)
	- Like (Unlike)
- PEER (All Active)
	### One-on-One Features (select)
	- DM
	- DM Thread
	- Follow
	- Unfollow
	- Send File
	- Invite to Game (TIC-TAC-TOE)
- Group
	- Create Group
	- Update Group
	- View my Groups
		- Send Message to Group
- Notifications (non-verbose messaging of non-urgent messages)

### Verbose-Mode
- Verbose Log (verbose messaging of all messages accordingly to LSNP specifications)
- Settings: Change Post TTL (change how post TTL are declared in-client)
- Revoke Token (enter token details to revoke)
- Terminate (exit)

### Important Notes
For Non-MAC Users, remove the line "self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)"





