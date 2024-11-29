from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from models import db, User, Service, CustomerProfile, Professional, ServiceRequest, Review

admin_bp = Blueprint('admin', __name__)
api = Api(admin_bp)

# Utility function to filter results
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



# Search Endpoint
class AdminSearchAPI(Resource):
    def get(self):
        search_query = request.args.get('query', '').strip().lower()
        category = request.args.get('category', '').strip()
        results = []

        # Query based on category
        if category == "Services":
            services = Service.query.all()
            results = [service.to_dict() for service in filter_results(services, search_query, ['name', 'description'])]
        elif category == "Customers":
            customers = CustomerProfile.query.options(db.joinedload(CustomerProfile.user)).all()
            results = [customer.user.to_dict() for customer in filter_results(customers, search_query, ['user.username', 'user.email', 'address'])]
        elif category == "Professionals":
            professionals = Professional.query.options(db.joinedload(Professional.user)).all()
            results = [professional.to_dict() for professional in filter_results(professionals, search_query, ['user.username', 'user.email', 'service_type'])]
        elif category == "Service Requests":
            requests = ServiceRequest.query.options(
                db.joinedload(ServiceRequest.service),
                db.joinedload(ServiceRequest.professional),
            ).all()
            results = [request.to_dict() for request in filter_results(requests, search_query, [
                'service.name', 'professional.username', 'service_status', 'location_pin_code', 'remarks'
            ])]
        elif category == "Reviews":
            reviews = Review.query.options(
                db.joinedload(Review.reviewer),
                db.joinedload(Review.reviewee),
                db.joinedload(Review.service_request),
            ).all()
            results = [
                {
                    "Reviewer": review.reviewer.username if review.reviewer else "N/A",
                    "Reviewee": review.reviewee.username if review.reviewee else "N/A",
                    "Rating": review.rating,
                    "Review": review.review,
                    "Service Request ID": review.service_request_id,
                    "Timestamp": review.timestamp.isoformat(),
                } for review in filter_results(reviews, search_query, ['review', 'rating', 'reviewer.username', 'reviewee.username'])
            ]
        else:
            return jsonify({"error": "Invalid category provided."}), 400

        return jsonify({"results": results})

# Add resource to API
api.add_resource(AdminSearchAPI, '/api/search')
