from core.token_validator import validate_token

posts = []
seen_post_ids = set()

def save_post(post: dict):
    post_id = post.get("MESSAGE_ID")

    if post_id in seen_post_ids:
        return False
    else:
        seen_post_ids.add(post_id)
        posts.append(post)

    return True

def get_recent_posts(limit=20):
    valid_posts = []

    for post in reversed(posts):
        token = post.get("TOKEN")
        if token and validate_token(token, "broadcast"):
            valid_posts.append(post)

        if (len(valid_posts) >= limit):
            break

    return valid_posts