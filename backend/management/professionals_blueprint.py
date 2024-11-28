from flask import Blueprint, request, jsonify
from models import db, Professional, User, Block

professionals_bp = Blueprint('professionals', __name__)

@professionals_bp.route('/api/professionals', methods=['GET'])
def get_verified_professionals():
    """Fetch all verified professionals."""
    professionals = Professional.query.filter_by(verified=True).all()
    result = []
    for prof in professionals:
        user = User.query.get(prof.user_id)
        result.append({
            "id": prof.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "service_type": prof.service_type,
            "experience": prof.experience,
            "verified": prof.verified,
            "average_rating": prof.average_rating,
            "blocked": prof.blocked,
        })
    return jsonify(result), 200

@professionals_bp.route('/api/professionals/block/<int:professional_id>', methods=['POST'])
def block_professional(professional_id):
    """Block or unblock a professional."""
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({"message": "Professional not found"}), 404

    professional.blocked = not professional.blocked
    if professional.blocked:
        block_entry = Block(blocked_user_id=professional.user_id)
        db.session.add(block_entry)
    else:
        Block.query.filter_by(blocked_user_id=professional.user_id).delete()

    db.session.commit()
    return jsonify({"message": "Professional block status updated"}), 200
