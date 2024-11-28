from flask import Blueprint, request, jsonify
from models import db, Professional
from flask_restful import Api, Resource, reqparse

# Create Blueprint for managing professionals' approval
professionals_pending_bp = Blueprint('professionals_pending', __name__)
api = Api(professionals_pending_bp)

class PendingProfessionalResource(Resource):
    def get(self):
        # Get all professionals who are not verified (verified = False)
        professionals = Professional.query.filter_by(verified=False).all()
        return jsonify([{
            'id': professional.id,
            'user_id': professional.user_id,
            'service_type': professional.service_type,
            'experience': professional.experience,
            'description': professional.description,
            'verified': professional.verified,
            'blocked': professional.blocked,
            'experience_proof': professional.experience_proof,
            'average_rating': professional.average_rating,
        } for professional in professionals])

    def put(self):
        # Approve or reject a professional (approve: verified=True, reject: delete)
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=True, help='Professional ID is required')
        parser.add_argument('action', type=str, required=True, choices=['approve', 'reject'], help="Action must be 'approve' or 'reject'")
        args = parser.parse_args()

        professional = Professional.query.get(args['id'])
        
        if not professional:
            return {"message": "Professional not found"}, 404
        
        if args['action'] == 'approve':
            professional.verified = True
            db.session.commit()
            return {"message": "Professional approved successfully"}, 200
        elif args['action'] == 'reject':
            db.session.delete(professional)
            db.session.commit()
            return {"message": "Professional rejected and deleted successfully"}, 200

api.add_resource(PendingProfessionalResource, '/professionals/pending')
