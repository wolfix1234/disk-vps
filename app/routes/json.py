import os
import re
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth import authorized
from ..utils.path import safe_path

bp = Blueprint('json', __name__)
logger = logging.getLogger(__name__)


# GET or POST JSON file content
@bp.route("/json", methods=["GET", "POST"])
def handle_json():
    if error := authorized(request, current_app.config["SECRET_TOKEN"]):
        return error

    store_id = request.headers.get("storeId")
    filename = request.headers.get("filename")

    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw filename: {repr(filename)}")

    if not store_id or not filename:
        return jsonify({"error": "Missing storeId or filename"}), 400

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())

    if not store_id or not filename:
        return jsonify({"error": "Invalid storeId or filename after sanitization"}), 400

    try:
        store_path, error = safe_path(current_app.config["UPLOAD_FOLDER"], store_id)
        if error:
            return error
        full_path = os.path.join(store_path, "json", filename)
    except Exception:
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
            logger.error(f"Error reading file: {str(e)}")
            return jsonify({"error": "Error reading file"}), 500

    elif request.method == "POST":
        if not os.path.isfile(full_path):
            return jsonify({"error": "File not found"}), 404
        if not request.is_json:
            return jsonify({"error": "No JSON data provided"}), 400

        new_data = request.get_json()
        try:
            json.dumps(new_data)  # Ensure serializable
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            temp_path = f"{full_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2)
            os.replace(temp_path, full_path)
            return jsonify({"message": "File updated successfully"}), 200
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Error updating file: {str(e)}")
            return jsonify({"error": "Error updating file"}), 500


# List all JSON files in a store
@bp.route("/list-json", methods=["GET"])
def list_json():
    if error := authorized(request, current_app.config["SECRET_TOKEN"]):
        return error

    store_id = request.headers.get("storeId")
    if not store_id:
        return jsonify({"error": "Missing storeId header"}), 400

    try:
        store_path, error = safe_path(current_app.config["UPLOAD_FOLDER"], store_id)
        if error:
            return error
        json_path = os.path.join(store_path, "json")
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    if not os.path.exists(json_path):
        return jsonify({"error": "Store ID does not exist"}), 404

    try:
        json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
        return jsonify({"json_files": json_files}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading JSON files: {str(e)}"}), 500


# Create or delete dynamic JSON files
@bp.route("/create-json", methods=["POST", "DELETE"])
def dynamic_json():
    if error := authorized(request, current_app.config["SECRET_TOKEN"]):
        return error

    store_id = request.headers.get("storeId")
    dynamic = request.headers.get("filename")

    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw dynamic: {repr(dynamic)}")

    if not store_id or not dynamic:
        return jsonify({"error": "Missing storeId or filename"}), 400

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    dynamic = re.sub(r'[^a-zA-Z0-9._-]', '', dynamic.strip())

    try:
        store_path, error = safe_path(current_app.config["UPLOAD_FOLDER"], store_id)
        if error:
            return error
        lg_path = os.path.join(store_path, "json", f"{dynamic}lg.json")
        sm_path = os.path.join(store_path, "json", f"{dynamic}sm.json")
    except Exception:
        return jsonify({"error": "Invalid path construction"}), 400

    # ========== POST ==========
    if request.method == "POST":
        if os.path.isfile(lg_path) or os.path.isfile(sm_path):
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

        def write_file(path):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                tmp = f"{path}.tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, indent=2)
                os.replace(tmp, path)
                return True, None
            except Exception as e:
                if os.path.exists(tmp):
                    os.remove(tmp)
                return False, str(e)

        ok_lg, err_lg = write_file(lg_path)
        ok_sm, err_sm = write_file(sm_path)

        if ok_lg and ok_sm:
            return jsonify({"message": f"{dynamic}lg.json and {dynamic}sm.json created"}), 201
        return jsonify({
            "error": "File creation failed",
            "lg_error": err_lg,
            "sm_error": err_sm
        }), 500

    # ========== DELETE ==========
    elif request.method == "DELETE":
        deleted = []
        not_found = []

        for path in [lg_path, sm_path]:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    deleted.append(os.path.basename(path))
                    logger.info(f"Deleted: {path}")
                except Exception as e:
                    logger.error(f"Delete failed: {str(e)}")
                    return jsonify({"error": f"Delete failed: {os.path.basename(path)}"}), 500
            else:
                not_found.append(os.path.basename(path))

        if deleted:
            return jsonify({
                "message": f"Deleted: {', '.join(deleted)}",
                "not_found": not_found
            }), 200
        return jsonify({"error": "No files found to delete"}), 404
