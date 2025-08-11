dms = []
seen_dm_ids = set()

def save_dm(dm: dict):
    message_id = dm.get("MESSAGE_ID")
    if not message_id or message_id in seen_dm_ids:
        return False
    
    seen_dm_ids.add(message_id)
    dms.append(dm)
    return True

def get_recent_dms(limit=50):
    return sorted(dms, key=lambda d: int(d.get("TIMESTAMP")), reverse=True)[:limit]

def get_thread(with_user_id: str, profile_user_id: str, limit=50):
    thread = [dm for dm in dms if
              (dm.get("FROM") == with_user_id and dm.get("TO") == profile_user_id) or
              (dm.get("FROM") == profile_user_id and dm.get("TO") == with_user_id)]
    return sorted(thread, key=lambda d: int(d.get("TIMESTAMP")))[-limit:]
