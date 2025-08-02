# TODO use these constants so that we don't have to replace everything everytime; add as you see fit.

# User Datagram Protocol Constants
PORT = 50999              # UDP port for LSNP communication
BROADCAST_INTERVAL = 300  # Seconds between PROFILE broadcasts; 5 MINUTES
BUFFER_SIZE = 1024        # Max bytes to receive in a UDP packet; 1 KB

# Token defaults
TOKEN_TTL_CHAT = 600       # 10 minutes for direct messages
TOKEN_TTL_BROADCAST = 300  # 5 minutes for posts

# Avatars
DEFAULT_AVATAR_TYPE = "none"

# Display / Debug
VERBOSE = True