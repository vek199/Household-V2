from flask import Blueprint, request, jsonify
from models import db, Service
from flask_restful import Api, Resource, reqparse

# Create Blueprint for services
services_bp = Blueprint('services', __name__)
api = Api(services_bp)

class ServiceResource(Resource):
    def get(self):
        services = Service.query.all()
        return jsonify([{
            'id': service.id,
            'name': service.name,
            'price': float(service.price),
            'time_required': service.time_required,
            'description': service.description,
        } for service in services])
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Service name is required")
        parser.add_argument('price', type=float, required=True, help="Service price is required")
        parser.add_argument('time_required', type=int, required=True, help="Time required for service is required")
        parser.add_argument('description', type=str, required=False, help="Description of the service")

        args = parser.parse_args()
        
        if Service.query.filter_by(name=args['name']).first():
            return {"message": "Service already exists"}, 400
        
        new_service = Service(
            name=args['name'],
            price=args['price'],
            time_required=args['time_required'],
            description=args.get('description', '')
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        return {"message": "Service Created Successfully"}, 201
    
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=True, help='Service id is required')
        parser.add_argument('name', type=str, required=False)
        parser.add_argument('price', type=float, required=False)
        parser.add_argument('time_required', type=int, required=False)
        parser.add_argument('description', type=str, required=False)

        args = parser.parse_args()
        
        service = Service.query.get(args['id'])
        
        if not service:
            return {"message": "Service not found"}, 404
        
        if args['name']:
            service.name = args['name']
        if args['price']:
            service.price = args['price']
        if args['time_required']:
            service.time_required = args['time_required']
        if args['description']:
            service.description = args['description']
        
        db.session.commit()
        
        return {"message": "Service updated successfully"}, 200
    
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=True, help='Service id is required')
        
        args = parser.parse_args()
        
        service = Service.query.get(args['id'])
        
        if not service:
            return {"message": "Service not found"}, 404
        
        db.session.delete(service)
        db.session.commit()
        
        return {"message": "Service deleted successfully"}, 200

api.add_resource(ServiceResource, '/service')
