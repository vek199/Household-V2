from flask import Blueprint, request, jsonify
from models import db, ServiceRequest, Service, User
from flask_restful import Api, Resource, reqparse

# Create Blueprint for managing service request history
service_request_hist_bp = Blueprint('service_request_history', __name__)
api = Api(service_request_hist_bp)

class ServiceRequestHistoryResource(Resource):
    def get(self, customer_id):
        # Get all service requests for the given customer
        service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).all()
        
        if not service_requests:
            return {"message": "No service requests found for this customer"}, 404

        return jsonify([sr.to_dict() for sr in service_requests])

    def post(self):
        # Add a new service request
        parser = reqparse.RequestParser()
        parser.add_argument('service_id', type=int, required=True, help='Service ID is required')
        parser.add_argument('customer_id', type=int, required=True, help='Customer ID is required')
        parser.add_argument('professional_id', type=int, required=True, help='Professional ID is required')
        parser.add_argument('service_status', type=str, required=True, help='Service status is required')
        parser.add_argument('remarks', type=str)
        args = parser.parse_args()

        # Ensure that the customer and professional exist
        customer = User.query.get(args['customer_id'])
        professional = User.query.get(args['professional_id'])

        if not customer:
            return {"message": "Customer not found"}, 404
        if not professional:
            return {"message": "Professional not found"}, 404

        # Create a new service request
        service_request = ServiceRequest(
            service_id=args['service_id'],
            customer_id=args['customer_id'],
            professional_id=args['professional_id'],
            service_status=args['service_status'],
            remarks=args['remarks']
        )

        db.session.add(service_request)
        db.session.commit()

        return jsonify(service_request.to_dict()), 201

# Add the resources to the API
api.add_resource(ServiceRequestHistoryResource, '/service_requests_hist/<int:customer_id>', endpoint='history')
api.add_resource(ServiceRequestHistoryResource, '/service_requests_hist', endpoint='add')
