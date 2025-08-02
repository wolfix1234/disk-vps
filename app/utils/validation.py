import re
from fastapi import HTTPException

def validate_id(name):
    if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise HTTPException(status_code=400, detail="Invalid storeId format")
    return True

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())