from flask import Blueprint, jsonify
from models import db, Service, Professional, User

service_pros_details_bp = Blueprint('service_pros_details', __name__)

@service_pros_details_bp.route('/service/<int:service_id>', methods=['GET'])
def get_service_and_professionals(service_id):
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"message": "Service not found"}), 404

    # Join Professional with User to get the username based on user_id
    professionals = Professional.query \
        .join(User, User.id == Professional.user_id) \
        .filter(Professional.service_type == service.name, Professional.verified == True) \
        .all()

    # Format the response to include the username along with other professional details
    return jsonify({
        "service": service.to_dict(),
        "professionals": [
            {
                "id": prof.id,
                "service_type": prof.service_type,
                "experience": prof.experience,
                "description": prof.description,
                "verified": prof.verified,
                "blocked": prof.blocked,
                "average_rating": prof.average_rating,
                "user": {
                    "id": prof.user.id,
                    "username": prof.user.username  # Include the username from the User model
                }
            }
            for prof in professionals
        ]
    })
