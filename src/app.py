import os
import sys

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO

from src import utils
from .config import get_config
from src.socketio_controller import io_connect, io_disconnect, io_join_room, io_on_message


sess = Session()
app = Flask(__name__, static_url_path="", static_folder="../client/build")

app.config.from_object(get_config())
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")



def run_app():
    utils.init_redis()
    sess.init_app(app)
    
    args = sys.argv[1:]
    port = os.environ.get("PORT", 5000)

    if len(args) > 0:
        try:
            port = int(args[0])
        except ValueError:
            pass
        
    socketio.run(app, port=port, debug=True, use_reloader=True)

socketio.on_event("connect", io_connect)
socketio.on_event("disconnect", io_disconnect)
socketio.on_event("room.join", io_join_room)
socketio.on_event("message", io_on_message)

from src import routes
application = app