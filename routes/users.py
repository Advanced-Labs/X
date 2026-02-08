from flask import Blueprint, jsonify, request

users_bp = Blueprint("users", __name__)

USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]

@users_bp.route("/", methods=["GET"])
def list_users():
    return jsonify(USERS)

@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)
