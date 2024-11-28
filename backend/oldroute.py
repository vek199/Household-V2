from flask import current_app as app, jsonify, render_template, request
from flask_security import auth_required, verify_password
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from models import *
from flask_restful import Api,Resource,reqparse

datastore = app.security.datastore

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
    
    user = datastore.find_user(username = username)
    
    if not user:
        return jsonify({"message" : "User does not exists in Database"}), 404

    if verify_password(password,user.password):
        return jsonify({'token':user.get_auth_token(),'username' : user.username, 'email' : user.email, 'role' : user.roles[0].name, 'id' : user.id})
    
    return jsonify({'message' : 'Password wrong'}),400

jwt = JWTManager(app)

# Store revoked tokens (in-memory for simplicity, can be a database)
revoked_tokens = set()

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Invalidate the token by adding it to the revoked tokens list.
    """
    jti = get_jwt()["jti"]  # Get the unique identifier for the JWT
    revoked_tokens.add(jti)  # Add the token identifier to the revoked list
    return jsonify({"message": "Successfully logged out"}), 200


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    """
    Check if the token is in the revoked tokens list.
    """
    jti = jwt_payload["jti"]
    return jti in revoked_tokens


@app.route('/register/customer', methods=['POST'])
def register_customer():
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


@app.route('/register/professional', methods=['POST'])
def register_professional():
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

    # Check if the user already exists
    existing_user = datastore.find_user(email=email)
    if existing_user:
        return jsonify({"message": "Email already registered"}), 400

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
    # Fetch all services
@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])

# Add a new service
@app.route('/api/services', methods=['POST'])
def add_service():
    data = request.json
    service = Service(name=data['name'], price=data['price'], description=data.get('description'))
    db.session.add(service)
    db.session.commit()
    return jsonify(service.to_dict()), 201

# Delete a service
@app.route('/api/services/<int:id>', methods=['DELETE'])
def delete_service(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({"message": "Service deleted"}), 200

# Fetch professionals pending approval
@app.route('/api/professionals/pending', methods=['GET'])
def get_pending_professionals():
    professionals = Professional.query.filter_by(verified=False).all()
    return jsonify([prof.to_dict() for prof in professionals])

# Approve a professional
@app.route('/api/professionals/approve/<int:id>', methods=['POST'])
def approve_professional(id):
    professional = Professional.query.get_or_404(id)
    professional.verified = True
    db.session.commit()
    return jsonify({"message": "Professional approved"}), 200

# Reject a professional
@app.route('/api/professionals/reject/<int:id>', methods=['POST'])
def reject_professional(id):
    professional = Professional.query.get_or_404(id)
    db.session.delete(professional)
    db.session.commit()
    return jsonify({"message": "Professional rejected"}), 200

# Fetch all customers
@app.route('/api/customers', methods=['GET'])
def get_customers():
    customers = CustomerProfile.query.all()
    return jsonify([customer.to_dict() for customer in customers])

# Block a customer
@app.route('/api/customers/block/<int:id>', methods=['POST'])
def block_customer(id):
    customer = CustomerProfile.query.get_or_404(id)
    customer.blocked = True
    db.session.commit()
    return jsonify({"message": "Customer blocked"}), 200

# Unblock a customer
@app.route('/api/customers/unblock/<int:id>', methods=['POST'])
def unblock_customer(id):
    customer = CustomerProfile.query.get_or_404(id)
    customer.blocked = False
    db.session.commit()
    return jsonify({"message": "Customer unblocked"}), 200

# Fetch all service requests
@app.route('/api/service-requests', methods=['GET'])
def get_service_requests():
    service_requests = ServiceRequest.query.all()
    return jsonify([request.to_dict() for request in service_requests])

# Fetch all professionals
@app.route('/api/professionals', methods=['GET'])
def get_professionals():
    professionals = Professional.query.all()
    return jsonify([prof.to_dict() for prof in professionals])