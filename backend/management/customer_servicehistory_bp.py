from flask import Blueprint, request, jsonify
from models import db, ServiceRequest, User, Professional
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

        # Include service name and professional details in the response
        response = [{
            'id': sr.id,
            'service_name': sr.service.name if sr.service else None,
            'customer_id': sr.customer_id,
            'professional_id': sr.professional_id,
            'professional_name': sr.professional.username if sr.professional else None,
            'professional_phone': sr.professional.phone_number if sr.professional else None,
            'service_status': sr.service_status,
            'remarks': sr.remarks,
            'date_of_request': sr.date_of_request,
            'date_closed': sr.date_closed,
        } for sr in service_requests]

        return jsonify(response)

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

        # Include service name and professional details in the response
        return jsonify({
            'id': service_request.id,
            'service_name': service_request.service.name if service_request.service else None,
            'professional_name': service_request.professional.username if service_request.professional else None,
            'professional_phone': service_request.professional.phone if service_request.professional else None,
            'service_status': service_request.service_status,
            'remarks': service_request.remarks,
            'date_of_request': service_request.date_of_request,
            'date_closed': service_request.date_closed,
        }), 201

    def put(self, service_request_id):
        # Retrieve the service request
        service_request = ServiceRequest.query.get(service_request_id)

        if not service_request:
            return {"message": "Service request not found"}, 404

        # Parse the incoming data
        data = request.get_json()
        action = data.get('action')

        if not action:
            return {"message": "Action is required"}, 400

        # Update the status based on the action
        if action == 'cancel':
            service_request.service_status = 'cancelled'
        elif action == 'close':
            service_request.service_status = 'closed'
            service_request.date_closed = db.func.now()  # Optional: Update the closed date
        else:
            return {"message": f"Invalid action '{action}'"}, 400

        # Commit the changes to the database
        db.session.commit()

        return jsonify({
            'id': service_request.id,
            'service_status': service_request.service_status,
            'remarks': service_request.remarks,
            'date_of_request': service_request.date_of_request,
            'date_closed': service_request.date_closed,
        })


# Add the resources to the API
api.add_resource(ServiceRequestHistoryResource, '/service_requests_hist/<int:customer_id>', endpoint='history')
api.add_resource(ServiceRequestHistoryResource, '/service_requests_hist', endpoint='add')
api.add_resource(ServiceRequestHistoryResource, '/service_request/<int:service_request_id>/action', endpoint='cancel')
api.add_resource(ServiceRequestHistoryResource, '/service_request/<int:service_request_id>/action', endpoint='close')
