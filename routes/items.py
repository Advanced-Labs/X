from flask import Blueprint, jsonify

items_bp = Blueprint("items", __name__)

ITEMS = [
    {"id": 1, "name": "Widget", "price": 9.99, "owner_id": 1},
    {"id": 2, "name": "Gadget", "price": 24.99, "owner_id": 2},
    {"id": 3, "name": "Doohickey", "price": 4.99, "owner_id": 1},
]

@items_bp.route("/", methods=["GET"])
def list_items():
    return jsonify(ITEMS)

@items_bp.route("/by-owner/<int:owner_id>", methods=["GET"])
def items_by_owner(owner_id):
    owned = [i for i in ITEMS if i["owner_id"] == owner_id]
    return jsonify(owned)
