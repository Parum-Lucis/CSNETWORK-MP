import json
from models.peer import Profile

def save_profile_to_file(profile: Profile, filename: str):
    with open(filename, "w") as f:
        json.dump(profile.to_dict(), f)

def load_profile_from_file(filename: str) -> Profile:
    with open(filename, "r") as f:
        data = json.load(f)
    return Profile(
        user_id=data["user_id"],
        ip=data["ip"],
        display_name=data["display_name"],
        status=data["status"],
        avatar_type=data.get("avatar_type"),
        avatar_data=data.get("avatar_data")
    )