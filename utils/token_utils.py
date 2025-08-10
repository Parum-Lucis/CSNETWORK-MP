import time

def generate_token(user_id: str, ttl: int, scope: str) -> str:
    """
    Generates an LSNP token (<USER_ID>|<UNIX_EXPIRY>|<SCOPE>) string given a time-to-live and scope.

    Args:
        user_id (str): The sender's unique identifier.
        ttl (int): Time-to-live in seconds
        scope (str): Purpose of the token

    Returns:
        str: A token string to embed in LSNP messages.
    """
    expiry = int(time.time()) + ttl
    return f"{user_id}|{expiry}|{scope}"

