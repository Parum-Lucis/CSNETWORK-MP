from config import DEFAULT_AVATAR_TYPE
class Profile:
    """
    a peer in the LSNP network.
    """
    def __init__(self, user_id, ip, display_name=None, status=None, avatar_type=None, avatar_data=None):
        """
        Initializes a Profile object with user details.

        Args:
            user_id (str): Unique identifier for the peer
            ip (str): IP address of the peer.
            display_name (str, optional): Friendly name to show (defaults to user_id).
            status (str, optional): Current status message (e.g., "Online", "Busy").
            avatar_type (str, optional): Type of avatar used (e.g., "ascii", "emoji").
            avatar_data (str, optional): Encoded avatar image or emoji.
        """
        self.user_id = user_id
        self.ip = ip
        self.display_name = display_name or user_id
        self.status = status or ""
        self.avatar_type = avatar_type
        self.avatar_data = avatar_data or DEFAULT_AVATAR_TYPE

    def to_dict(self):
        """
        Converts the Profile object to a dictionary.

        Returns:
           dict: Dictionary containing all profile fields.
        """
        return{
            "user_id": self.user_id,
            "ip": self.ip,
            "display_name": self.display_name,
            "status": self.status,
            "avatar_type": self.avatar_type,
            "avatar_data": self.avatar_data
        }

    @staticmethod
    def from_message(msg: dict, addr) -> "Profile":
        """
        Creates a Profile object from a parsed LSNP PROFILE message.

        Args:
            msg (dict): Parsed key-value message (from parse_message()).
            addr (tuple): Address tuple (IP, port) from the UDP packet.

        Returns:
            Profile: A new Profile instance.
        """
        return Profile(
            user_id=msg.get("USER_ID"),
            ip =addr[0],
            display_name = msg.get("DISPLAY_NAME"),
            status=msg.get("STATUS"),
            avatar_type=msg.get("AVATAR_TYPE"),
            avatar_data=msg.get("AVATAR_DATA")
        )

    def __str__(self):
        """
        Returns a human-readable string representation of the peer status.
        """
        return f"{self.display_name}: {self.status}"