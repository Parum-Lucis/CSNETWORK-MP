user_followers = set()
user_following = set()

def add_follower(user_id: str):
    user_followers.add(user_id)

def remove_follower(user_id: str):
    user_followers.discard(user_id)

def is_follower(user_id: str):
    return user_id in user_followers

def add_following(user_id: str):
    user_following.add(user_id)

def remove_following(user_id: str):
    user_following.discard(user_id)

def is_following(user_id: str):
    return user_id in user_following

def get_followers():
    return list(user_followers)

def get_following():
    return list(user_following)