import os
import re
from PIL import Image
from fastapi import UploadFile

ALLOWED_EXTENSIONS = {'webp', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename(filename):
    """Secure a filename by removing unsafe characters."""
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename

async def save_image(file: UploadFile, full_path: str):
    temp_path = f"{full_path}.tmp"
    try:
        # Read file content
        content = await file.read()
        
        # Save to temporary file
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Verify image
        with Image.open(temp_path) as img:
            img.verify()
        
        # Move to final location
        os.rename(temp_path, full_path)
        return True, None
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, str(e)