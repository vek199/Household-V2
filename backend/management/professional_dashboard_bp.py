from flask import Blueprint, request
from flask_restful import Api, Resource
from models import db, Professional, ServiceRequest, CustomerProfile

# Initialize the blueprint
professional_dashboard_bluep = Blueprint('professional_dashboard_bp', __name__, url_prefix='/api/professional')
api = Api(professional_dashboard_bluep)

class ServiceRequests(Resource):
    def get(self, professional_id):
        # Validate if the professional exists
        # Fetch service requests grouped by status
        service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()
        print(service_requests)
        # Organize service requests into categories
        response_data = {
            'active': None,  # Only one active service request is allowed
            'requested': [],
            'closed': []
        }

        for request in service_requests:
            customer = CustomerProfile.query.filter_by(user_id=request.customer_id).first()
            print(customer)
            request_data = {
                'id': request.id,
                'customer_name': customer.user.username,
                'contact_no': customer.user.phone_number,
                'location': customer.location_pin_code,
                'date': request.date_of_request.strftime('%Y-%m-%d') if request.date_of_request else 'N/A',
                'rating': request.reviews[0].rating if request.reviews else 'Not rated',
                'status': request.service_status
            }

            if request.service_status == 'assigned':
                response_data['active'] = request_data
            elif request.service_status == 'requested':
                response_data['requested'].append(request_data)
            elif request.service_status == 'closed':
                response_data['closed'].append(request_data)

        return response_data, 200

    def post(self, professional_id):
        # Handle status updates for a specific service request
        data = request.json
        print(f"Received data: {data}")

        service_request_id = data.get('service_request_id')
        action = data.get('action')  # 'accept' or 'reject'

        if not service_request_id or not action:
            return {'message': 'service_request_id and action are required'}, 400

        # Fetch the service request
        service_request = ServiceRequest.query.filter_by(id=service_request_id, professional_id=professional_id).first()

        if not service_request:
            return {'message': 'Service request not found'}, 404

        # Handle actions: accept or reject
        if action == 'accept':
            # Check for already assigned service
            assigned_request = ServiceRequest.query.filter_by(professional_id=professional_id, service_status='assigned').first()
            if assigned_request:
                return {'message': f'Cannot accept. Service {assigned_request.id} is already assigned.'}, 400
            service_request.service_status = 'assigned'
        elif action == 'reject':
            service_request.service_status = 'cancelled'  # Changed to 'cancelled' instead of 'rejected'
        else:
            return {'message': 'Invalid action'}, 400

        # Commit changes to the database
        db.session.commit()

        # Return success message
        return {'message': f'Service request {action}ed successfully'}, 200


# Register the API resource
api.add_resource(ServiceRequests, '/service_requests/<int:professional_id>')






# from flask import Blueprint, request
# from flask_restful import Api, Resource
# from models import *
# from flask_security import current_user

# # Initialize the blueprint
# professional_dashboard_bluep = Blueprint('professional_dashboard_bp', __name__, url_prefix='/api/professional')
# api = Api(professional_dashboard_bluep)

# class ClosedServices(Resource):
#     def get(self, professional_id):
#         # No need to fetch from request.args anymore
#         professional = Professional.query.get_or_404(professional_id)
#         professional_id = professional.user_id
#         closed_requests = ServiceRequest.query.filter_by(professional_id=professional_id, service_status='closed').all()
        
#         # Formatting the response
#         result = []
#         for request in closed_requests:
#             customer = CustomerProfile.query.filter_by(user_id=request.customer_id).first()
#             result.append({
#                 'id': request.id,
#                 'customer_name': customer.user.username,
#                 'service_status': request.service_status,
#                 'contact_no': customer.user.phone_number,
#                 'location': customer.location_pin_code,
#                 'date': request.date_closed.strftime('%Y-%m-%d') if request.date_closed else 'N/A',
#                 'rating': request.reviews[0].rating if request.reviews else 'Not rated'
#             })

#         return {'closed_services': result}, 200

# class TodayServices(Resource):
#     def get(self, professional_id):
#         professional = Professional.query.get_or_404(professional_id)
#         professional_id = professional.user_id
#         requested_services = ServiceRequest.query.filter_by(professional_id=professional_id, service_status='requested').all()

#         result = []
#         for request in requested_services:
#             customer = CustomerProfile.query.filter_by(user_id=request.customer_id).first()
#             result.append({
#                 'id': request.id,
#                 'service_status': request.service_status,
#                 'customer_name': customer.user.username,
#                 'contact_no': customer.user.phone_number,
#                 'location': customer.location_pin_code,
#                 'action': 'accept' if not request.service_status == 'assigned' else 'assigned'
#             })
        
#         return {'today_services': result}, 200

#     def post(self, professional_id):
#         professional = Professional.query.get_or_404(professional_id)
#         professional_id = professional.user_id
#         service_request_id = request.json.get('service_request_id')
#         action = request.json.get('action')  # 'accept' or 'reject'

#         if not service_request_id or not action:
#             return {'message': 'service_request_id and action are required'}, 400

#         service_request = ServiceRequest.query.filter_by(id=service_request_id, professional_id=professional_id).first()

#         if not service_request:
#             return {'message': 'Service request not found'}, 404

#         # Check if there's an already assigned service
#         if action == 'accept':
#             assigned_request = ServiceRequest.query.filter_by(professional_id=professional_id, service_status='assigned').first()
#             if assigned_request:
#                 return {'message': f'Cannot accept. Service {assigned_request.id} is already assigned.'}, 400
#             service_request.service_status = 'assigned'
#         elif action == 'reject':
#             service_request.service_status = 'rejected'
#         else:
#             return {'message': 'Invalid action'}, 400

#         db.session.commit()

#         return {'message': f'Service request {action}ed successfully'}, 200


# class CurrentServices(Resource):
#     def get(self, professional_id):
#         professional = Professional.query.get_or_404(professional_id)
#         professional_id = professional.user_id
#         # Get the assigned service for the professional (only one should be assigned)
#         assigned_request = ServiceRequest.query.filter_by(professional_id=professional_id, service_status='assigned').first()

#         if assigned_request:
#             customer = CustomerProfile.query.filter_by(user_id=assigned_request.customer_id).first()
#             return {
#                 'current_service': {
#                     'id': assigned_request.id,
#                     'service_status': assigned_request.service_status,
#                     'customer_name': customer.user.username,
#                     'contact_no': customer.user.phone_number,
#                     'location': customer.location_pin_code,
#                 }
#             }, 200

#         return {'message': 'No current service assigned'}, 404

# # Add the resources to the API
# api.add_resource(ClosedServices, '/closed_services/<int:professional_id>')
# api.add_resource(TodayServices, '/today_services/<int:professional_id>')
# api.add_resource(CurrentServices, '/current_services/<int:professional_id>')
