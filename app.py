import os
import shutil
import json
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import uuid


app = Flask(__name__)
CORS(app, resources={r"/uploads/*": {"origins": ["http://localhost:3000"]}, r"/upload/*": {"origins": ["http://localhost:3000"]}, r"/delete/*": {"origins": ["http://localhost:3000"]}})

UPLOAD_FOLDER = "uploads"
TEMPLATE_FOLDER = "templates"
SECRET_TOKEN = "your-secret-token"


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions



def authorized(req):
    auth_header = req.headers.get("Authorization")
    return auth_header and auth_header.split(" ")[1] == SECRET_TOKEN


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

    # Check if file was actually uploaded
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Validate store exists
    store_path = os.path.join(UPLOAD_FOLDER, store_id)
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
        base_path = os.path.abspath(UPLOAD_FOLDER)
        full_path = os.path.abspath(os.path.join(base_path, store_id, 'image', filename))

        # Verify path stays within allowed directory
        if not full_path.startswith(base_path):
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





@app.route("/uploads/<store_id>/<action>/<filename>", methods=["GET"])
def get_uploaded_file(store_id, action, filename):
    directory = os.path.join(UPLOAD_FOLDER, store_id, action)
    return send_from_directory(directory, filename)




@app.route("/images/<store_id>", methods=["GET"])
def get_image_names(store_id):
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Build and validate safe path
    try:
        base_path = os.path.abspath(UPLOAD_FOLDER)
        image_path = os.path.abspath(os.path.join(base_path, store_id, "image"))
        if not image_path.startswith(base_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    # Check if directory exists
    if not os.path.exists(image_path):
        return jsonify({"error": f"Store ID {store_id} does not exist"}), 404

    # Get list of image files
    try:
        image_files = [f for f in os.listdir(image_path) if allowed_file(f)]
        return jsonify({"images": image_files}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading images: {str(e)}"}), 500





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
        base_path = os.path.abspath(UPLOAD_FOLDER)
        file_path = os.path.abspath(os.path.join(base_path, store_id, "image", filename))
        if not file_path.startswith(base_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    # Delete operation
    try:
        if not os.path.exists(file_path):
            return jsonify({"error": "Image not found on disk"}), 404
        if not os.path.isfile(file_path):
            return jsonify({"error": "Path is not a file"}), 400

        os.remove(file_path)
        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error deleting image: {str(e)}"}), 500





@app.route("/init-store", methods=["GET"])
def init_store():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.headers.get("Store-Id")
    if not store_id:
        return jsonify({"error": "Missing Store-Id in header"}), 400

    store_path = os.path.join(UPLOAD_FOLDER, store_id)
    store_json_path = os.path.join(store_path, "json")

    if os.path.exists(store_json_path):
        return jsonify({"message": "Store already exists"}), 200

    os.makedirs(store_json_path, exist_ok=True)

    for filename in os.listdir(TEMPLATE_FOLDER):
        if filename.endswith(".json"):
            src = os.path.join(TEMPLATE_FOLDER, filename)
            dst = os.path.join(store_json_path, filename)
            shutil.copyfile(src, dst)

    return jsonify({"message": "Store initialized with templates" , "url": f"http://91.216.104.8/{store_id}/json"}), 200


@app.route("/json", methods=["GET", "POST"])
def handle_json():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    store_id = request.args.get("storeId")
    filename = request.args.get("filename")

    # Validate inputs
    if not store_id or not filename:
        return jsonify({"error": "Missing storeId or filename"}), 400

    # Secure the filename and store_id
    safe_filename = secure_filename(filename)
    safe_store_id = secure_filename(store_id)

    # Verify the secured values match the originals
    if safe_filename != filename or safe_store_id != store_id:
        return jsonify({"error": "Invalid characters in filename or storeId"}), 400

    # Build safe path
    try:
        base_path = os.path.abspath(UPLOAD_FOLDER)
        full_path = os.path.abspath(os.path.join(base_path, safe_store_id, "json", safe_filename))

        # Verify the final path is within the allowed directory
        if not full_path.startswith(base_path):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    if request.method == "GET":
        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        try:
            with open(full_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return jsonify({"error": "File is empty"}), 400
                f.seek(0)
                data = json.load(f)
            return jsonify(data), 200
        except json.JSONDecodeError:
            return jsonify({"error": "File contains invalid JSON"}), 400
        except Exception:
            return jsonify({"error": "Error reading file"}), 500

    elif request.method == "POST":
        # Only allow updates to existing files
        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        new_data = request.get_json()
        if new_data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        try:
            # Validate JSON by dumping to string first
            json.dumps(new_data)

            # Write to temporary file first for atomic update
            temp_path = f"{full_path}.tmp"
            with open(temp_path, "w") as f:
                json.dump(new_data, f, indent=2)

            # Atomic replace of original file
            os.replace(temp_path, full_path)

            return jsonify({"message": "File updated successfully"}), 200
        except ValueError as e:
            return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": f"Error updating file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)