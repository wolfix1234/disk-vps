import os
import shutil
import json
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import re
from pathlib import Path



logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"/uploads/*": {"origins": ["http://localhost:3000"]}, r"/upload/*": {"origins": ["http://localhost:3000"]}, r"/delete/*": {"origins": ["http://localhost:3000"]}})
load_dotenv() 


# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["100 per day", "10 per minute"]
# )

# limiter.init_app(app)




app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
TEMPLATE_FOLDER =  os.getenv("TEMPLATE_FOLDER")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
VPS_URL = os.getenv("VPS_URL")



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_id(name):
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))



def authorized(req):
    auth_header = req.headers.get("Authorization")
    return auth_header and auth_header.split(" ")[1] == SECRET_TOKEN


def safe_path(base, *parts):
    base_path = Path(base).resolve()
    full_path = Path(base, *parts).resolve()
    if base_path not in full_path.parents and base_path != full_path:
        raise ValueError("Invalid path")
    return str(full_path)


#@app.route('/', methods=['GET'])
#def index():
#    return Response(b"Hi, beach!", mimetype='text/plain')

@app.route('/upload/image', methods=['POST'])
def upload_image():
    # Authentication check
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Validate required fields
    if 'storeId' not in request.form:
        return jsonify({"error": "Missing storeId"}), 400
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    

    store_id = request.form['storeId']
    file = request.files['file']
    
    if not validate_id(store_id):
        return jsonify({"error": "Invalid storeId format"}), 400

    # Check if file was actually uploaded
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({"error": "File too large"}), 400

    # Validate store exists
    store_path = safe_path(UPLOAD_FOLDER, store_id)
    if not os.path.exists(store_path):
        return jsonify({"error": f"Store ID {store_id} does not exist"}), 404

    # Secure the filename
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Validate file extension
    if not allowed_file(filename):
        return jsonify({"error": "File type not allowed. Only PNG, JPG, JPEG, GIF are accepted"}), 400

    # Build safe path
    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        full_path = os.path.abspath(os.path.join(store_path,'image', filename))

        # Verify path stays within allowed directory
        if not full_path.startswith(store_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid path construction"}), 400

    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Save file with atomic write and image validation
    temp_path = f"{full_path}.tmp"
    try:
        # First save to temporary location
        file.save(temp_path)

        # Verify the file is actually an image
        try:
            with Image.open(temp_path) as img:
                img.verify()  # Verify it's an image
        except Exception:
            os.remove(temp_path)
            return jsonify({"error": "Uploaded file is not a valid image"}), 400

        # If validation passes, move to final location
        os.rename(temp_path, full_path)

        return jsonify({
            "message": "Image uploaded successfully",
            "path": f"{store_id}/image/{filename}",
            "storeId": store_id,
            "filename": filename,
            "size": os.path.getsize(full_path)
        }), 200
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": f"Error saving image: {str(e)}"}), 500





# @app.route("/uploads/<store_id>/<action>/<filename>", methods=["GET"])
# def get_uploaded_file(store_id, action, filename):
#     directory = os.path.join(UPLOAD_FOLDER, store_id, action)
#     return send_from_directory(directory, filename)




@app.route("/images/<store_id>", methods=["GET"])
def get_image_names(store_id):
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    if not validate_id(store_id):
        return jsonify({"error": "Invalid storeId format"}), 400

    # Build and validate safe path
    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        image_path = os.path.abspath(os.path.join(store_path, "image"))
        if not image_path.startswith(store_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400
    
    # Check if directory exists
    if not os.path.exists(store_path):
        return jsonify({"error": f"Store ID {store_id} does not exist"}), 404

    # Get list of image files
    try:
        image_files = [f for f in os.listdir(image_path) if allowed_file(f)]
        return jsonify({"images": image_files}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading images, no image on {store_id}"}), 500





@app.route("/delete/image", methods=["DELETE"])
def delete_image():
    # Authentication
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Get required fields from JSON
    store_id = request.json.get("storeId")
    filename = request.json.get("filename")

    # Validate required parameters
    if not all([store_id, filename]):
        return jsonify({"error": "Missing storeId or filename"}), 400

    # Build and validate safe path
    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        file_path = os.path.abspath(os.path.join(store_path ,"image", filename))
        if not file_path.startswith(store_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    # Delete operation
    try:
        if not os.path.exists(file_path):
            return jsonify({"error": "Image not found"}), 404
        if not os.path.isfile(file_path):
            return jsonify({"error": "Path is not a file"}), 400

        os.remove(file_path)
        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error deleting image"}), 500





@app.route("/init-store", methods=["GET"])
def init_store():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.headers.get("storeId")
    if not store_id:
        return jsonify({"error": "Missing storeId in header"}), 400

    store_path = safe_path(UPLOAD_FOLDER, store_id)
    store_json_path = os.path.join(store_path, "json")

    if os.path.exists(store_json_path):
        return jsonify({"message": "Store already exists"}), 200
    
    #if not os.path.exists(store_json_path):
     #   return jsonify({"error": f"Store ID {store_id} does not exist"}), 404

    os.makedirs(store_json_path, exist_ok=True)

    for filename in os.listdir(TEMPLATE_FOLDER):
        if filename.endswith(".json"):
            src = os.path.join(TEMPLATE_FOLDER, filename)
            dst = os.path.join(store_json_path, filename)
            shutil.copyfile(src, dst)

    return jsonify({"message": "Store initialized with templates" , "url": f"{VPS_URL}/{store_id}/json"}), 200




# get file content and update file content

@app.route("/json", methods=["GET", "POST"])
def handle_json():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.headers.get("storeId")
    filename = request.headers.get("filename")
    
    logging.info(f"Raw store_id: {repr(store_id)}")
    logging.info(f"Raw filename: {repr(filename)}")

    # Validate inputs
    if not store_id or not filename:
        return jsonify({"error": "Missing storeId or filename"}), 400

    # Sanitize inputs: keep only alphanumeric, underscores, hyphens, dots
    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())
    
    # Validate sanitized inputs
    if not store_id or not filename:
        return jsonify({"error": "Invalid storeId or filename after sanitization"}), 400

    if not all(c.isalnum() or c in '._-' for c in store_id) or \
       not all(c.isalnum() or c in '._-' for c in filename):
        return jsonify({"error": "Invalid characters in storeId or filename"}), 400

    logging.info(f"Cleaned store_id: {store_id}")
    logging.info(f"Cleaned filename: {filename}")

    # Build and validate path
    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        full_path = safe_path(store_path, "json", filename)
    except ValueError:
        return jsonify({"error": "Invalid path construction"}), 400

    if request.method == "GET":
        if not os.path.isfile(full_path):
            return jsonify({"error": "File not found"}), 404

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return jsonify({"error": "File is empty"}), 400
                f.seek(0)
                data = json.load(f)
            return jsonify(data), 200
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
        except Exception as e:
            logging.error(f"Error reading file: {str(e)}")
            return jsonify({"error": "Error reading file"}), 500

    elif request.method == "POST":
        if not os.path.isfile(full_path):
            return jsonify({"error": "File not found"}), 404

        if not request.is_json:
            return jsonify({"error": "No JSON data provided"}), 400

        new_data = request.get_json()
        try:
            # Validate JSON
            json.dumps(new_data)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write to temporary file
            temp_path = f"{full_path}.tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, indent=2)
                os.replace(temp_path, full_path)
                return jsonify({"message": "File updated successfully"}), 200
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except ValueError as e:
            return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
        except Exception as e:
            logging.error(f"Error updating file: {str(e)}")
            return jsonify({"error": "Error updating file"}), 500
    
    
    
@app.route("/list-json", methods=["GET"])
def list_json():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.headers.get("storeId")
    if not store_id:
        return jsonify({"error": "Missing storeId header"}), 400

    # Build and validate safe path
    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        json_path = os.path.abspath(os.path.join(store_path, "json"))
        if not json_path.startswith(store_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    # Check if directory exists
    if not os.path.exists(json_path):
        return jsonify({"error": "Store ID does not exist"}), 404

    # Get list of JSON files
    try:
        json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
        return jsonify({"json_files": json_files}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading JSON files: {str(e)}"}), 500
    
    
    

@app.route("/create-json", methods=["POST", "DELETE"])
def dynamic_json():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.headers.get("storeId")
    dynamic = request.headers.get("filename")

    logging.info(f"Raw store_id: {repr(store_id)}")
    logging.info(f"Raw dynamic: {repr(dynamic)}")

    if not store_id or not dynamic:
        return jsonify({"error": "Missing storeId or filename"}), 400

    # Sanitize inputs
    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    dynamic = re.sub(r'[^a-zA-Z0-9._-]', '', dynamic.strip())

    if not store_id or not dynamic:
        return jsonify({"error": "Invalid storeId or filename after sanitization"}), 400

    if not all(c.isalnum() or c in '._-' for c in store_id) or \
       not all(c.isalnum() or c in '._-' for c in dynamic):
        return jsonify({"error": "Invalid characters in storeId or filename"}), 400

    logging.info(f"Cleaned store_id: {store_id}")
    logging.info(f"Cleaned dynamic: {dynamic}")

    try:
        store_path = safe_path(UPLOAD_FOLDER, store_id)
        fulllg_path = safe_path(store_path, "json", f"{dynamic}lg.json")
        fullsm_path = safe_path(store_path, "json", f"{dynamic}sm.json")
    except ValueError:
        return jsonify({"error": "Invalid path construction"}), 400

    # ========== POST: CREATE ==========
    if request.method == "POST":
        if os.path.isfile(fulllg_path) or os.path.isfile(fullsm_path):
            return jsonify({"error": "File already exists"}), 409

        default_content = {
            "children": {
                "type": f"{dynamic}",
                "metaData": {
                    "title": f"{dynamic}",
                    "description": f"{dynamic} page"
                },
                "sections": [],
                "order": []
            }
        }

        def write_json_file(file_path):
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                temp_path = f"{file_path}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, indent=2)
                os.replace(temp_path, file_path)
                return True, None
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False, str(e)

        success_lg, err_lg = write_json_file(fulllg_path)
        success_sm, err_sm = write_json_file(fullsm_path)

        if success_lg and success_sm:
            return jsonify({"message": f"Files {dynamic}lg.json and {dynamic}sm.json created successfully"}), 201
        else:
            return jsonify({
                "error": "File creation failed",
                "lg_error": err_lg,
                "sm_error": err_sm
            }), 500

    # ========== DELETE ==========
    elif request.method == "DELETE":
        deleted_files = []
        not_found_files = []

        for path in [fulllg_path, fullsm_path]:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    deleted_files.append(os.path.basename(path))
                    logging.info(f"Deleted file: {path}")
                except Exception as e:
                    logging.error(f"Failed to delete file {path}: {str(e)}")
                    return jsonify({"error": f"Failed to delete {os.path.basename(path)}"}), 500
            else:
                not_found_files.append(os.path.basename(path))

        if deleted_files:
            return jsonify({
                "message": f"Deleted files: {', '.join(deleted_files)}",
                "not_found": not_found_files
            }), 200
        else:
            return jsonify({"error": "No files found to delete"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
