import os
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'webp', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, full_path):
    temp_path = f"{full_path}.tmp"
    try:
        file.save(temp_path)
        with Image.open(temp_path) as img:
            img.verify()
        os.rename(temp_path, full_path)
        return True, None
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, str(e)