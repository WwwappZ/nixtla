from flask import request, jsonify
from functools import wraps
from config import Config
def require_apikey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Authorization') == Config.API_KEY:
            return view_function(*args, **kwargs)
        return jsonify({"error": "Unauthorized access"}), 403
    return decorated_function

