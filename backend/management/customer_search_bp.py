from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from sqlalchemy.orm import joinedload
from models import db, CustomerProfile, Professional, Service, ServiceRequest


customer_bp = Blueprint('customer', __name__)
api = Api(customer_bp)


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


# Customer Search API
class CustomerSearchAPI(Resource):
    def get(self):
        search_query = request.args.get('query', '').strip().lower()
        if not search_query:
            return jsonify({"results": []})

        category = request.args.get('category', '').strip().lower()
        results = []

        # Search Professionals
        if category in ["all", "professionals"]:
            professionals = Professional.query.options(joinedload(Professional.user)).all()
            results += [
                {
                    "id": professional.id,
                    "username": professional.user.username,
                    "email": professional.user.email,
                    "service_type": professional.service_type,
                    "rating": professional.average_rating,
                }
                for professional in filter_results(
                    professionals,
                    search_query,
                    ['user.username', 'user.email', 'service_type']
                )
            ]

        # Search Services
        if category in ["all", "services"]:
            services = Service.query.all()
            results += [
                {
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "price": float(service.price),  # Include price as additional info
                }
                for service in filter_results(
                    services,
                    search_query,
                    ['name', 'description']
                )
            ]

        # Search Service Requests
        if category in ["all", "service requests"]:
            requests = ServiceRequest.query.options(
                joinedload(ServiceRequest.service),
                joinedload(ServiceRequest.professional),
            ).all()
            results += [
                {
                    "id": request.id,
                    "service_name": request.service.name if request.service else "N/A",
                    "professional_name": request.professional.username if request.professional else "N/A",
                    "status": request.service_status,
                    "remarks": request.remarks,
                    "date_of_request": request.date_of_request.isoformat(),
                }
                for request in filter_results(
                    requests,
                    search_query,
                    ['service.name', 'professional.username', 'remarks', 'service_status']
                )
            ]

        return jsonify({"results": results})


# Add resource to API
api.add_resource(CustomerSearchAPI, '/api/customer_search')
