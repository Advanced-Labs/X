from flask import Blueprint, jsonify
from api.common_ref import get_low_stock_threshold

items_bp = Blueprint("items", __name__)

ITEMS = [
    {"id": 1, "name": "Widget", "price": 9.99, "owner_id": 1, "category_id": 1, "quantity": 10},
    {"id": 2, "name": "Gadget", "price": 24.99, "owner_id": 2, "category_id": 2, "quantity": 0},
    {"id": 3, "name": "Doohickey", "price": 4.99, "owner_id": 1, "category_id": 3, "quantity": 3},
]

@items_bp.route("/", methods=["GET"])
def list_items():
    return jsonify(ITEMS)

@items_bp.route("/by-owner/<int:owner_id>", methods=["GET"])
def items_by_owner(owner_id):
    owned = [i for i in ITEMS if i["owner_id"] == owner_id]
    return jsonify(owned)

@items_bp.route("/by-category/<int:category_id>", methods=["GET"])
def items_by_category(category_id):
    matched = [i for i in ITEMS if i["category_id"] == category_id]
    return jsonify(matched)

@items_bp.route("/low-stock", methods=["GET"])
def low_stock_items():
    threshold = get_low_stock_threshold()
    low = [i for i in ITEMS if i["quantity"] < threshold]
    return jsonify(low)
