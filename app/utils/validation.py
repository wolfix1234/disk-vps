import re
from flask import jsonify

def validate_id(name):
    if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, jsonify({"error": "Invalid storeId format"}), 400
    return True, None

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())