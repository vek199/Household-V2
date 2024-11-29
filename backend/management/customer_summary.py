from flask import Blueprint, jsonify, request  # Ensure request is imported
from flask_restful import Api, Resource
from sqlalchemy.orm import joinedload
from models import db, CustomerProfile, Professional, Service, ServiceRequest

customer_sum_bp = Blueprint('customer_sum', __name__)
api = Api(customer_sum_bp)

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
class ServiceRequestStatusAPI(Resource):
    def get(self):
        
        print(request)  # This should now work if 'request' is imported
        customer_id = request.args.get('user_id', type=int)
        customer = CustomerProfile.query.get_or_404(customer_id)
        user_id = customer.user.id
        print(id)
        
        # Query service requests for the specific user
        statuses = ['closed', 'requested', 'assigned']
        service_requests =ServiceRequest.query.filter(ServiceRequest.customer_id == customer_id).all()
        print(service_requests)
        
        customer_data = {}
        for req in service_requests:
            customer = req.customer
            if not customer:
                continue
            customer_info = {
                "id": customer.id,
                "username": customer.username,
                "email": customer.email,
                "phone_number": customer.phone_number,
            }
            if customer.id not in customer_data:
                customer_data[customer.id] = {
                    "customer": customer_info,
                    "requests": {
                        "closed": 0,
                        "requested": 0,
                        "assigned": 0,
                        "cancelled": 0
                        
                    },
                }
            customer_data[customer.id]["requests"][req.service_status] += 1

        response = [
            {"customer": data["customer"], "requests": data["requests"]}
            for data in customer_data.values()
        ]
        return jsonify(response)

# Add resource to API
api.add_resource(ServiceRequestStatusAPI, '/api/service_request_status')
