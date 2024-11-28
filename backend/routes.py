from flask import current_app as app, jsonify, render_template, request
from flask_security import auth_required, verify_password
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from flask_restful import Api, Resource, reqparse
from models import *
import uuid
import os
from werkzeug.utils import secure_filename
from datetime import datetime

datastore = app.security.datastore
jwt = JWTManager(app)
api = Api(app)

# Store revoked tokens (in-memory for simplicity, can be a database)
revoked_tokens = set()

@app.route('/')
def home():
    return render_template('index.html')

@app.get('/protected')
@auth_required('token')
def protected():
    return '<h1> only accessible by auth user </h1>'

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message" : "Invalid Username or Password for login"}), 404
    
    user = datastore.find_user(username=username)
    
    if not user:
        return jsonify({"message" : "User does not exists in Database"}), 404

    if verify_password(password, user.password):
        return jsonify({'token': user.get_auth_token(), 'username' : user.username, 'email' : user.email, 'role' : user.roles[0].name, 'id' : user.id})
    
    return jsonify({'message' : 'Password wrong'}), 400


# Token revocation for logout
@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    auth_header = request.headers.get('Authorization')
    print(f"Received Authorization Header: {auth_header}")
    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 422
    jti = get_jwt()["jti"]
    revoked_tokens.add(jti)  # Assuming you maintain a token revocation list
    return jsonify({"message": "Successfully logged out"}), 200

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    """
    Check if the token is in the revoked tokens list.
    """
    jti = jwt_payload["jti"]
    return jti in revoked_tokens


# API Resources for registration and management
class CustomerRegister(Resource):
    def post(self):
        data = request.get_json()
        
        # Extract and validate data from the request
        username = data.get('username')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        address = data.get('address')
        location_pin_code = data.get('location_pin_code')
        preferred_services = data.get('preferred_services')
        
        if not all([username, phone_number, email, password, confirm_password, address, location_pin_code]):
            return jsonify({"message": "All fields are required"}), 400
        
        if password != confirm_password:
            return jsonify({"message": "Passwords do not match"}), 400
        
        # Check if the user already exists
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"message": "Email already registered"}), 400

        # Create the new user
        try:
            new_user = datastore.create_user(
                username=username,
                phone_number=phone_number,
                email=email,
                password=password,
                roles=['customer']  # Assign customer role
            )

            # Create customer profile
            customer_profile = CustomerProfile(
                user_id=new_user.id,
                address=address,
                location_pin_code=location_pin_code,
                preferred_services=preferred_services
            )
            db.session.add(customer_profile)
            db.session.commit()

            return jsonify({"message": "Customer registration successful"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Registration failed: {str(e)}"}), 500


class ProfessionalRegister(Resource):
    def post(self):
        data = request.form.to_dict()
        file = request.files.get('experience_proof')

        # Extract and validate data from the request
        username = data.get('username')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        service_type = data.get('service_type')
        experience = data.get('experience')
        description = data.get('description')

        if not all([username, phone_number, email, password, confirm_password, service_type, experience, description]):
            return jsonify({"message": "All fields are required"}), 400

        if password != confirm_password:
            return jsonify({"message": "Passwords do not match"}), 400

        if not file or not allowed_file(file.filename):
            return jsonify({"message": "Invalid or missing experience proof file"}), 400

        # Save the file
        try:
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            sanitized_username = secure_filename(username.replace(" ", "_"))
            unique_filename = f"{sanitized_username}_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}"
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
        except Exception as e:
            return jsonify({"message": f"File upload failed: {str(e)}"}), 500

        # Create the new user and professional profile
        try:
            new_user = datastore.create_user(
                username=username,
                phone_number=phone_number,
                email=email,
                password=password,
                roles=['professional']  # Assign professional role
            )

            professional_profile = Professional(
                user_id=new_user.id,
                service_type=service_type,
                experience=experience,
                description=description,
                experience_proof=unique_filename
            )
            db.session.add(professional_profile)
            db.session.commit()

            return jsonify({"message": "Professional registration successful"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Registration failed: {str(e)}"}), 500

class ServiceList(Resource):
    def get(self):
        services = Service.query.all()
        return jsonify([service.to_dict() for service in services])

    def post(self):
        data = request.json
        service = Service(name=data['name'], price=data['price'], description=data.get('description'))
        db.session.add(service)
        db.session.commit()
        return jsonify(service.to_dict()), 201


class ServiceDetail(Resource):
    def delete(self, id):
        service = Service.query.get_or_404(id)
        db.session.delete(service)
        db.session.commit()
        return jsonify({"message": "Service deleted"}), 200


class ProfessionalApproval(Resource):
    def post(self, id):
        professional = Professional.query.get_or_404(id)
        professional.verified = True
        db.session.commit()
        return jsonify({"message": "Professional approved"}), 200


class ProfessionalRejection(Resource):
    def post(self, id):
        professional = Professional.query.get_or_404(id)
        db.session.delete(professional)
        db.session.commit()
        return jsonify({"message": "Professional rejected"}), 200



# Add the Resources to the API
api.add_resource(CustomerRegister, '/register/customer')
api.add_resource(ProfessionalRegister, '/register/professional')
api.add_resource(ServiceList, '/api/services')
api.add_resource(ServiceDetail, '/api/services/<int:id>')
api.add_resource(ProfessionalApproval, '/api/professionals/approve/<int:id>')
api.add_resource(ProfessionalRejection, '/api/professionals/reject/<int:id>')

# Add more routes as needed
# You can also implement similar structure for other resources like ServiceRequests, Customers, etc.
