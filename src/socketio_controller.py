import json
from flask import session
from flask_socketio import emit, join_room

from src import utils



def publish(name, message, broadcast=False, room=None):
    if room:
        emit(name, message, room=room, broadcast=True)
    else:
        emit(name, message, broadcast=broadcast)
        
    outgoing = {"serverId": utils.SERVER_ID, "type": name, "data": message}
    utils.redis_client.publish('MESSAGES', json.dumps(outgoing))
    

def io_connect():
    user = session.get("user", None)
    
    if not user:
        return
    
    user_id = user.get("id", None)
    utils.redis_client.sadd("online_users", user_id)
    
    msg = dict(user)
    msg["online"] = True
    
    publish("user.connected", msg, broadcast=True)
    
    
def io_disconnect():
    user = session.get("user", None)
    if user:
        utils.redis_client.srem("online_users", user["id"])
    
        msg = dict(user)
        msg["online"] = False
        publish("user.disconnected", msg, broadcast=True)
        
        
def io_join_room(id_room):
    join_room(id_room)
    
    
def io_on_message(message):
    utils.redis_client.sadd("online_users", message["from"])
    message_string = json.dumps(message)
    room_id = message['roomId']
    room_key = f"room:{room_id}"
    
    is_private = not bool(utils.redis_client.exists(f"{room_key}:name"))
    room_has_messages = bool(utils.redis_client.exists(room_key))
    
    if is_private and not room_has_messages:
        ids = room_id.split(":")
        msg = {
            "id": room_id,
            "names": [
                utils.hmget(f"user:{ids[0]}", "username"),
                utils.hmget(f"user:{ids[1]}", "username"),
            ],
        }
        publish("show.room", msg, broadcast=True)
    
    utils.redis_client.zadd(room_key, {message_string: int(message["date"])})

    if is_private:
        publish("message", message, room=room_id)
    else:
        publish("message", message, broadcast=True)
        