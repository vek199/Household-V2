from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from models import db, Professional, ServiceRequest, Review
from sqlalchemy.orm import joinedload

professional_sum_bp = Blueprint('professional_sum', __name__)
api = Api(professional_sum_bp)

# Utility function to filter results (can be used in future if needed)
def filter_results(items, search_query, fields):
    results = []
    for item in items:
        for field in fields:
            value = item
            try:
                for attr in field.split('.'):
                    value = getattr(value, attr, None)
                if value and search_query in str(value).lower():
                    results.append(item)
                    break
            except AttributeError:
                continue  # Skip if the attribute doesn't exist
    return results

class ProfessionalSummaryAPI(Resource):
    def get(self):
        # Fetch logged-in user's id from request
        user_id = request.args.get('user_id', type=int)
        
        # Query for the professional record
        professional = Professional.query.filter_by(user_id=user_id).first()
        
        if not professional:
            return jsonify({"message": "Professional not found"}), 404
        
        # Calculate average rating for the professional
        reviews = Review.query.filter_by(reviewee_id=user_id).all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            average_rating = round(total_rating / len(reviews), 2)
        else:
            average_rating = None  # No ratings yet
        
        # Get service requests for the professional
        service_requests = ServiceRequest.query.filter_by(professional_id=user_id).all()
        
        # Prepare status counts for the service requests
        statuses = {
            "closed": 0,
            "requested": 0,
            "assigned": 0,
            "cancelled": 0
        }
        
        for req in service_requests:
            if req.service_status in statuses:
                statuses[req.service_status] += 1
        
        # Prepare the response data
        professional_summary = {
            "professional_id": professional.id,
            "user_id": user_id,
            "service_type": professional.service_type,
            "experience": professional.experience,
            "description": professional.description,
            "verified": professional.verified,
            "blocked": professional.blocked,
            "average_rating": average_rating,
            "statuses": statuses  # Include service request statuses
        }
        
        # Returning as JSON response
        return jsonify(professional_summary)

# Add resource to API
api.add_resource(ProfessionalSummaryAPI, '/api/professional_summary')
