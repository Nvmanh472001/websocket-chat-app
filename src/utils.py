import json
import math
import random as rd

import bcrypt

from .config import get_config
from src import fetch_data

SERVER_ID = rd.uniform(0, 322321)
redis_client = get_config().redis_client


def make_username_key(username):
    return f"username:{username}"


def create_user(username, password):
    username_key = make_username_key(username)
    
    hashed_password = bcrypt.hashpw(str(password).encode("utf-8"), bcrypt.gensalt(10))
    next_id = redis_client.incr("total_users")
    user_key = f"user:{next_id}"
    
    redis_client.set(username_key, user_key)
    redis_client.hmset(user_key, {"username": username, "password": hashed_password})
    
    redis_client.sadd(f"user:{next_id}:rooms", "0")
    
    return {"id": next_id, "username": username}

def get_messages(room_id=0, offset=0, size=50):
    room_key = f"room_key:{room_id}"
    room_exists = redis_client.exists(room_key)
    
    if not room_exists:
        return []
    else:
        values = redis_client.zrevrange(room_key, offset, offset + size)
        return list(map(lambda x: json.loads(x.decode("utf-8")), values))
    
def hmget(key, key2):
    result = redis_client.hmget(key, key2)
    
    return list(map(lambda x: x.decode("utf-8"), result))

def get_private_room_id(user1, user2):
    if math.isnan(user1) or math.isnan(user2) or user1 == user2:
        return None
    return f"{min(user1, user2)}:{max(user1, user2)}"

def create_private_room(user1, user2):
    room_id = get_private_room_id(user1, user2)
    if not room_id:
        return None, True

    redis_client.sadd(f"user:{user1}:rooms", room_id)
    redis_client.sadd(f"user:{user2}:rooms", room_id)

    return (
        {
            "id": room_id,
            "names": [
                hmget(f"user:{user1}", "username"),
                hmget(f"user:{user2}", "username"),
            ],
        },
        False,
    )

def init_redis():
    total_users_exist = redis_client.exists("total_users")
    if not total_users_exist:
        redis_client.set("total_users", 0)
        redis_client.set(f"room:0:name", "General")
        
        fetch_data.create()

def event_stream():
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("MESSAGES")
    
    for message in pubsub.listen():
        message_parsed = json.loads(message["data"])
        if message_parsed["serverId"] == SERVER_ID:
            continue

        data = "data:  %s\n\n" % json.dumps(
            {"type": message_parsed["type"], "data": message_parsed["data"],}
        )
        yield data