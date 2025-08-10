import time
from utils.printer import verbose_log

revoked_tokens = set()

def parse_token(token: str):
    """
    Parses an LSNP token string into components.

    Args:
        token (str): The raw token string to parse.

    Returns:
        tuple:
            user_id (str): The user ID who generated the token.
            expiry (int): The UNIX timestamp when the token expires.
            scope (str): The scope of the token (e.g., 'chat', 'senders').

        If the token is incomplete, returns empty tuple.
    """
    try:
        user_id, expiry, scope = token.split("|")
        expiry = int(expiry)
        return user_id, expiry, scope
    except Exception:
        return None, None, None

"""
    Validates a given LSNP token based on
        format USER_ID | UNIX_EXPIRY | SCOPE, 
        scope, 
        expiration, 
        and revocation status.
    
    Args:
        token (str): The raw token string to validate.
        expected_scope (str): The required scope (e.g., 'chat', 'senders').
    
    Returns:
        bool: 
            True if the token is valid and authorized for the requested scope
            False otherwise.
"""
def validate_token(token: str, expected_scope: str) -> bool:
    user_id, expiry, scope = parse_token(token)
    current_time = int(time.time())

    if not all([user_id, expiry, scope]):
        verbose_log("DROP!", f"Malformed token: {token}")
        return False

    if scope != expected_scope:
        verbose_log("DROP!", f"Scope mismatch: got '{scope}', expected '{expected_scope}'")
        return False

    if current_time > expiry:
        verbose_log("DROP!", f"Expired token for {user_id} (expired at {expiry})")
        return False

    if token in revoked_tokens:
        verbose_log("DROP!", f"Revoked token used by {user_id}")
        return False

    return True

def revoke_token(token):
    revoked_tokens.add(token)