from flask import jsonify

def authorized(request, secret_token):
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()

    # Handle missing, malformed, or incorrect token
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    elif len(parts) == 1:
        token = parts[0]
    else:
        return jsonify({"error": "Unauthorized"}), 401

    if token != secret_token:
        return jsonify({"error": "Unauthorized"}), 401

    return None  # Authorized
