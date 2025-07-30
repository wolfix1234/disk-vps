import os
import shutil
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth import authorized
from ..utils.path import safe_path

bp = Blueprint('store', __name__)

@bp.route("/init-store", methods=["GET"])
def init_store():
    """Initialize a store by copying JSON templates into its directory."""
    if error := authorized(request, current_app.config['SECRET_TOKEN']):
        return error

    store_id = request.headers.get("storeId")
    if not store_id:
        return jsonify({"error": "Missing storeId in header"}), 400

    store_path, error = safe_path(current_app.config['UPLOAD_FOLDER'], store_id)
    if error:
        return error

    store_json_path = os.path.join(store_path, "json")
    if os.path.exists(store_json_path):
        return jsonify({"message": "Store already exists"}), 200

    try:
        os.makedirs(store_json_path, exist_ok=True)

        template_folder = current_app.config['TEMPLATE_FOLDER']
        for filename in os.listdir(template_folder):
            if filename.endswith(".json"):
                src = os.path.join(template_folder, filename)
                dst = os.path.join(store_json_path, filename)
                shutil.copyfile(src, dst)

        vps_url = current_app.config['VPS_URL']
        return jsonify({
            "message": "Store initialized with templates",
            "url": f"{vps_url}/{store_id}"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to initialize store: {str(e)}"}), 500
