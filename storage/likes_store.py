likes = {}

def key(poster_user_id: str, post_ts: int):
    return (poster_user_id, int(post_ts))

def add_like(poster_user_id: str, post_ts: int, from_user_id: str):
    k = key(poster_user_id, post_ts)
    s = likes.get(k)

    if s is None:
        s = set()
        likes[k] = s
    
    s.add(from_user_id)

def remove_like(poster_user_id: str, post_ts: int, from_user_id: str):
    k = key(poster_user_id, post_ts)
    s = likes.get(k)

    if s:
        s.discard(from_user_id)
        if not s:
            likes.pop(k, None)

def get_like_count(poster_user_id: str, post_ts: int):
    return len(likes.get(key(poster_user_id, post_ts), set()))

def get_likers(poster_user_id: str, post_ts: int):
    return list(likes.get(key(poster_user_id, post_ts), set()))

