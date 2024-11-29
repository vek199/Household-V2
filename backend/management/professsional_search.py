from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from sqlalchemy.orm import joinedload
from models import db, ServiceRequest, Professional

professional_search_bp = Blueprint('professional_search', __name__)
api = Api(professional_search_bp)
def filter_service_requests(requests, search_query, fields):
    results = []
    for service_request in requests:
        for field in fields:
            try:
                # Dynamically access nested attributes
                value = service_request
                for attr in field.split('.'):
                    value = getattr(value, attr, None)
                # Check for matches
                if value and search_query in str(value).lower():
                    results.append(service_request)
                    break  # Stop checking other fields if a match is found
            except AttributeError:
                continue  # Skip if attribute is not found
    return results

class ProfessionalSearchAPI(Resource):
    def get(self):
        professional_id = request.args.get('professional_id', type=int)
        search_query = request.args.get('query', '').strip().lower()
        category = request.args.get('category', '').strip().lower()
        
        professional = Professional.query.get_or_404(professional_id)
        professional_id = professional.user.id
        
        if not professional_id:
            return jsonify({"error": "Professional ID is required"}), 400

        # Fetch service requests assigned to the professional
        service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).options(
            joinedload(ServiceRequest.service),
            joinedload(ServiceRequest.customer),
        ).all()

        # Filter results based on search query and category
        if search_query:
            fields = []
            if category == "date":
                fields = ["date_of_request", "date_closed"]
            elif category == "location":
                fields = ["customer.customer.address", "remarks"]
            elif category == "pincode":
                fields = ["customer.customer.location_pin_code"]
            elif category == "status":  # Check service_status as well
                fields = ["service_status"]
            elif category == "username":  # Check service_status as well
                fields = ["customer.customer.username"]
            else:  # Default: search across multiple fields
                fields = ["service.name", "customer.customer.username", "customer.customer.address", "remarks", "service_status"]

            service_requests = filter_service_requests(service_requests, search_query, fields)

        # Serialize the results
        results = [
            {
                "id": req.id,
                "service_name": req.service.name if req.service else "N/A",
                "customer_name": req.customer.username if req.customer else "N/A",
                "customer_address": req.customer.customer.address if req.customer.customer else "N/A",
                "customer_location": req.customer.customer.location_pin_code if req.customer.customer else "N/A",
                "date_of_request": req.date_of_request.isoformat() if req.date_of_request else "N/A",
                "date_closed": req.date_closed.isoformat() if req.date_closed else "N/A",
                "service_status": req.service_status,
                "remarks": req.remarks or "N/A",
            }
            for req in service_requests
        ]

        return jsonify({"results": results})

# Add resource to API
api.add_resource(ProfessionalSearchAPI, '/api/professional_search')
