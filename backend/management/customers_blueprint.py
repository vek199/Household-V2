from flask import Blueprint, jsonify
from models import db, CustomerProfile, User, Block

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/api/customers', methods=['GET'])
def get_customers():
    """Fetch all customers."""
    customers = CustomerProfile.query.all()
    result = []
    for customer in customers:
        user = User.query.get(customer.user_id)
        result.append({
            "id": customer.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": customer.address,
            "location_pin_code": customer.location_pin_code,
            "blocked": customer.blocked,
        })
    return jsonify(result), 200

@customers_bp.route('/api/customers/block/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    """Block or unblock a customer."""
    customer = CustomerProfile.query.get(customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    customer.blocked = not customer.blocked
    if customer.blocked:
        block_entry = Block(blocked_user_id=customer.user_id)
        db.session.add(block_entry)
    else:
        Block.query.filter_by(blocked_user_id=customer.user_id).delete()

    db.session.commit()
    return jsonify({"message": "Customer block status updated"}), 200
