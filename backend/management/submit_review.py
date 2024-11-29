from flask import Blueprint, request, jsonify
from models import db, Review, ServiceRequest

review_bp = Blueprint('review', __name__)

@review_bp.route('/review', methods=['POST'])
def submit_review():
    data = request.get_json()
    service_request_id = data['service_request_id']

    # Fetch the corresponding service request
    service_request = ServiceRequest.query.get(service_request_id)
    if not service_request:
        return jsonify({"error": "Service request not found"}), 404

    # Update service request status to 'closed'
    service_request.service_status = 'closed'

    # Create a new review entry
    new_review = Review(
        service_request_id=service_request.id,
        reviewer_id=data['reviewer_id'],
        reviewee_id=data['reviewee_id'],
        rating=data['rating'],
        review=data.get('review', ''),
    )
    db.session.add(new_review)
    db.session.commit() 

    return jsonify({"message": "Review submitted and service request closed successfully"}), 201
