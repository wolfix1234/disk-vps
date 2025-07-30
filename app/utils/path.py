from pathlib import Path
from flask import jsonify

def safe_path(base, *parts):
    try:
        base_path = Path(base).resolve()
        full_path = Path(base, *parts).resolve()
        if base_path not in full_path.parents and base_path != full_path:
            return None, jsonify({"error": "Invalid path"}), 400
        return str(full_path), None
    except Exception:
        return None, jsonify({"error": "Invalid path construction"}), 400