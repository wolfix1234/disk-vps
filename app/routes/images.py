import os
import logging
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth import authorized
from ..utils.file import allowed_file, save_image
from ..utils.path import safe_path
from ..utils.validation import validate_id, sanitize_filename

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('images', __name__)

@bp.route('/upload/image', methods=['POST'])
def upload_image():
    """Upload an image to a store's image directory."""
    if error := authorized(request, current_app.config['SECRET_TOKEN']):
        return error

    store_id = request.form.get('storeId')
    file = request.files.get('file')
    
    if not store_id or not file:
        return jsonify({"error": "Missing storeId or file"}), 400
    
    valid, error = validate_id(store_id)
    if not valid:
        return error
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file.content_length > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({"error": "File too large"}), 400
    
    filename = sanitize_filename(file.filename)
    if not filename or not allowed_file(filename):
        return jsonify({"error": "Invalid filename or file type"}), 400
    
    store_path, error = safe_path(current_app.config['UPLOAD_FOLDER'], store_id)
    if error:
        return error
    
    if not os.path.exists(store_path):
        return jsonify({"error": f"Store ID {store_id} does not exist"}), 404
    
    full_path = os.path.join(store_path, 'image', filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    success, error = save_image(file, full_path)
    if not success:
        logger.error(f"Error saving image for store_id {store_id}: {error}")
        return jsonify({"error": f"Error saving image: {error}"}), 500
    
    logger.info(f"Image uploaded successfully for store_id: {store_id}, filename: {filename}")
    return jsonify({
        "message": "Image uploaded successfully",
        "path": f"{store_id}/image/{filename}",
        "storeId": store_id,
        "filename": filename,
        "size": os.path.getsize(full_path)
    }), 200


@bp.route("/images", methods=["GET"])
def get_image_names():
    """List all images in a store's image directory."""
    if error := authorized(request, current_app.config['SECRET_TOKEN']):
        return error

    store_id = request.headers.get("storeId")
    if not store_id:
        return jsonify({"error": "Missing storeId in headers"}), 400

    valid, error = validate_id(store_id)
    if not valid:
        return error

    store_path, error = safe_path(current_app.config['UPLOAD_FOLDER'], store_id)
    if error:
        return error

    if not os.path.exists(store_path):
        return jsonify({"error": f"Store ID {store_id} does not exist"}), 404

    image_path = os.path.join(store_path, "image")
    try:
        image_files = [f for f in os.listdir(image_path) if allowed_file(f)]
        logger.info(f"Listed images for store_id: {store_id}")
        return jsonify({"images": image_files}), 200
    except Exception as e:
        logger.error(f"Error listing images for store_id {store_id}: {str(e)}")
        return jsonify({"error": f"Error reading images for {store_id}"}), 500


@bp.route("/delete/image", methods=["DELETE"])
def delete_image():
    """Delete an image from a store's image directory."""
    if error := authorized(request, current_app.config['SECRET_TOKEN']):
        return error

    store_id = request.json.get("storeId")
    filename = request.json.get("filename")

    if not all([store_id, filename]):
        return jsonify({"error": "Missing storeId or filename"}), 400
    
    valid, error = validate_id(store_id)
    if not valid:
        return error
    
    filename = sanitize_filename(filename)
    if not filename or not allowed_file(filename):
        return jsonify({"error": "Invalid filename"}), 400

    store_path, error = safe_path(current_app.config['UPLOAD_FOLDER'], store_id)
    if error:
        return error

    file_path = os.path.join(store_path, "image", filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Image not found"}), 404
    if not os.path.isfile(file_path):
        return jsonify({"error": "Path is not a file"}), 400

    try:
        os.remove(file_path)
        logger.info(f"Deleted image: {file_path}")
        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting image {file_path}: {str(e)}")
        return jsonify({"error": "Error deleting image"}), 500
