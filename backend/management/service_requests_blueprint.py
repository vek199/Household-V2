from flask import Blueprint, request, jsonify
from models import db, ServiceRequest, User, Service, Review
from flask_restful import Api, Resource, reqparse
from datetime import datetime

# Create Blueprint for service requests
service_requests_bp = Blueprint('service_requests', __name__)
api = Api(service_requests_bp)

class ServiceRequestResource(Resource):
    def get(self):
        service_requests = ServiceRequest.query.all()
        return jsonify([{
            'id': sr.id,
            'service': sr.service.name,
            'assigned_professional': f'{sr.professional.username}',
            'requested_date': sr.date_of_request,
            'status': sr.service_status,
            'customer_rating': self.get_customer_rating(sr.id),
            'professional_rating': self.get_professional_rating(sr.id)
        } for sr in service_requests])
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('service_id', type=int, required=True, help="Service ID is required")
        parser.add_argument('customer_id', type=int, required=True, help="Customer ID is required")
        parser.add_argument('professional_id', type=int, required=True, help="Professional ID is required")
        parser.add_argument('service_status', type=str, required=True, help="Service status is required")
        parser.add_argument('remarks', type=str, required=False, help="Remarks")

        args = parser.parse_args()

        # Create a new service request
        new_request = ServiceRequest(
            service_id=args['service_id'],
            customer_id=args['customer_id'],
            professional_id=args['professional_id'],
            service_status=args['service_status'],
            remarks=args.get('remarks', ''),
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return {"message": "Service request created successfully"}, 201

    def get_customer_rating(self, service_request_id):
        reviews = Review.query.filter_by(service_request_id=service_request_id).all()
        customer_reviews = [review for review in reviews if review.reviewer_id == self.get_customer_id_for_service_request(service_request_id)]
        if customer_reviews:
            return sum([review.rating for review in customer_reviews]) / len(customer_reviews)
        return None

    def get_professional_rating(self, service_request_id):
        reviews = Review.query.filter_by(service_request_id=service_request_id).all()
        professional_reviews = [review for review in reviews if review.reviewer_id == self.get_professional_id_for_service_request(service_request_id)]
        if professional_reviews:
            return sum([review.rating for review in professional_reviews]) / len(professional_reviews)
        return None

api.add_resource(ServiceRequestResource, '/service_request')
