# TODO use these constants so that we don't have to replace everything everytime; add as you see fit.

# User Datagram Protocol Constants
PORT = 50999              # UDP port for LSNP communication
BROADCAST_INTERVAL = 30  # Seconds between PROFILE broadcasts; 5 MINUTES
BUFFER_SIZE = 1024        # Max bytes to receive in a UDP packet; 1 KB

# Token defaults; 
TOKEN_TTL_CHAT = 600       # 10 minutes for direct messages
TOKEN_TTL_BROADCAST = 300  # 5 minutes for posts
token_ttl_post = 3600 # can be changed

# Avatars
DEFAULT_AVATAR_TYPE = "none"
MAX_AVATAR_SIZE = 20 * 1024 #20 KB

# Display / Debug
VERBOSE = True
def toggle_verbose():
    global VERBOSE
    VERBOSE = not VERBOSE
    return VERBOSE