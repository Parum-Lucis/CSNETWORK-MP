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
├── main.py
│ - Application entry point; initializes system components and starts the program.
│
├── config.py
│ - Centralized configuration (constants, environment variables, settings).
│
├── core/ # Core system logic
│ ├── ack_registry.py - Tracks acknowledgments for sent/received messages.
│ ├── dispatcher.py - Routes incoming messages to the correct handler.
│ ├── token_validator.py - Validates security/authentication tokens.
│ ├── udp_broadcast.py - Sends broadcast messages over UDP.
│ └── udp_singleton.py - Manages a single UDP listener instance.
│
├── handlers/ # Modules for handling specific message types
│ ├── ack_handler.py - Processes acknowledgment messages.
│ ├── direct_message_handler.py - Handles incoming direct/private messages.
│ ├── file_handler.py - Handles file transfer requests and data.
│ ├── game_handler.py - Manages multiplayer game-related messages.
│ ├── group_handler.py - Handles group chat or group event messages.
│ ├── ping_handler.py - Responds to ping requests to check peer status.
│ ├── post_handler.py - Processes social post-type messages.
│ └── profile_handler.py - Handles peer profile updates and queries.
│
├── senders/ # Modules for sending specific data types
│ ├── direct_message_unicast.py - Sends a direct/private message to a specific peer.
│ ├── game_invite_unicast.py - Sends a game invite to a specific peer.
│ ├── group_unicast.py - Sends messages to a group of peers.
│ ├── ping_broadcast.py - Sends ping requests to all reachable peers.
│ ├── post_broadcast.py - Broadcasts posts to the network.
│ └── profile_broadcast.py - Broadcasts profile updates to peers.
│
├── models/ # Data model definitions
│ ├── file_transfer.py - Model for file transfer metadata and state.
│ ├── game_session.py - Model representing an active or past game session.
│ ├── group.py - Model for a peer group and its metadata.
│ ├── message.py - Generic message object with metadata.
│ └── peer.py - Model for a peer (user/device) in the network.
│
├── storage/ # Local persistence and caching
│ ├── dm_store.py - Stores direct message history.
│ ├── group_directory.py - Stores information about groups.
│ ├── message_store.py - General message storage.
│ ├── peer_directory.py - Keeps track of known peers.
│ ├── post_store.py - Stores social posts.
│ ├── revocation_list.py - Stores revoked tokens or keys.
│ └── user_followers.py - Tracks followers/following relationships.
│
├── ui/ # User-facing interfaces
│ └── cli.py - Command-line interface for interacting with the system.
│
└── utils/ # Helper functions and utilities
├── base64_utils.py - Functions for Base64 encoding/decoding.
├── message_builder.py - Functions to construct message payloads.
├── network_utils.py - Helper functions for network-related tasks.
├── printer.py - Utility for formatted console output/logging.
├── profile_utils.py - Helper functions for profile operations.
├── time_utils.py - Date/time formatting and conversion helpers.
└── token_utils.py - Token creation, parsing, and validation helpers.		
	

## Running the Project
In terminal in the project directory, call python main.py

Enter a user name and set verbose mode on/off

## CLI Commands

Once inside the main menu, you can traverse via arrow keys/WASD and enter to interact with the user interface:

### Macro-Social Features
- POST (broadcast post to all followers)
- CHECK FEED (read posts of following & group?)
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



