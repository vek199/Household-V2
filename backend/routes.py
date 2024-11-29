from flask import current_app as app, jsonify, render_template, request
from flask_security import auth_required, verify_password
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, get_jwt
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

@app.route('/api/auth/current_user', methods=['GET'])
@jwt_required()  # or other authentication method
def get_current_user():
    current_user = get_jwt_identity()  # Fetch user from JWT identity
    user = User.query.get(current_user)  # Get user from DB
    return jsonify(user.to_dict())

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

@app.route('/api/customer/<int:id>', methods=['GET'])
def get_customer_details(id):
    customer = CustomerProfile.query.options(joinedload(CustomerProfile.user)).filter_by(id=id).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    profile_picture_url = f"https://api.generated.photos/api/v1/faces?api_key=YOUR_API_KEY&limit=1"  # Add actual profile pic API if needed.
    data = customer.to_dict()
    data["profile_picture"] = profile_picture_url
    data["user"] = customer.user.to_dict()
    return data

@app.route('/api/professional/<int:id>', methods=['GET'])
def get_professional_details(id):
    professional = Professional.query.options(joinedload(Professional.user)).filter_by(id=id).first()
    if not professional:
        return {"error": "Professional not found"}, 404

    profile_picture_url = f"https://api.generated.photos/api/v1/faces?api_key=YOUR_API_KEY&limit=1"
    data = professional.to_dict()
    data["profile_picture"] = profile_picture_url
    data["user"] = professional.user.to_dict()
    return data

@app.route('/api/customer_ratings', methods=['GET'])
def get_customer_ratings():
    # Calculate the overall average rating for customer satisfaction
    overall_avg_rating = db.session.query(
        db.func.avg(Review.rating).label('overall_avg_rating')
    ).scalar()  # `scalar()` fetches the single aggregated value
    
    # Return a JSON response with the overall rating
    return jsonify({'overall_customer_satisfaction': float(overall_avg_rating) if overall_avg_rating else 0.0})


@app.route('/api/professional_ratings', methods=['GET'])
def get_professional_ratings():
    data = db.session.query(
        Professional.id,
        User.username,
        db.func.avg(Review.rating).label('avg_rating')
    ).join(User, Professional.user_id == User.id).join(
        Review, Review.reviewee_id == User.id
    ).group_by(Professional.id).all()
    print('DATA:',data)
    return jsonify({user: float(avg_rating) for _, user, avg_rating in data})

@app.route('/api/service_requests_summary', methods=['GET'])
def get_service_requests_summary():
    data = db.session.query(
        ServiceRequest.service_status,
        db.func.count(ServiceRequest.id).label('count')
    ).group_by(ServiceRequest.service_status).all()
    
    return jsonify({status: count for status, count in data})


# Add the Resources to the API
api.add_resource(CustomerRegister, '/register/customer')
api.add_resource(ProfessionalRegister, '/register/professional')
api.add_resource(ServiceList, '/api/services')
api.add_resource(ServiceDetail, '/api/services/<int:id>')
api.add_resource(ProfessionalApproval, '/api/professionals/approve/<int:id>')
api.add_resource(ProfessionalRejection, '/api/professionals/reject/<int:id>')

# Add more routes as needed
# You can also implement similar structure for other resources like ServiceRequests, Customers, etc.
