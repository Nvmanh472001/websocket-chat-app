from functools import wraps

from flask import jsonify, session

def auth_middleware(next_func):
    @wraps(next_func)
    def __auth_middleware(*args, **kwargs):
        if not session["user"]:
            return jsonify(None), 403
        
        return next_func(*args, **kwargs)
    
    return __auth_middleware