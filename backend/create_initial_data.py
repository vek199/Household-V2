from flask import current_app as app
from models import *
from flask_security import SQLAlchemyUserDatastore, hash_password
    # Push app context    
with app.app_context():
    db.create_all()

    userdatastore : SQLAlchemyUserDatastore = app.security.datastore
    
    if not User.query.filter_by(username='admin').first():
        # Create customer and professional roles
        admin_role = userdatastore.find_or_create_role(
                name='admin',
                description='Super User'
            )
        customer_role = userdatastore.find_or_create_role(
                name='customer',
                description='customer'
            )
        professional_role = userdatastore.find_or_create_role(
                name='professional',
                description='Service professional'
            )
        db.session.commit()
            
        admin_user = userdatastore.create_user(
                username='admin',
                email='admin@example.com',
                password=hash_password('admin'),  
                fs_uniquifier=str(uuid.uuid4()),
                roles=[admin_role],
                confirmed_at=datetime.utcnow(),
            )
        db.session.commit()
            # Create customers
        customer1 = userdatastore.create_user(
                username='vek',
                email='customer1@example.com',
                phone_number='1234567890',
                password=hash_password('vek'),
                fs_uniquifier=str(uuid.uuid4()),
                roles=[customer_role],
                confirmed_at=datetime.utcnow(),
            )
        customer2 = userdatastore.create_user(
                username='cus2',
                email='customer2@example.com',
                phone_number='9876543210',
                password=hash_password('cus2'),
                fs_uniquifier=str(uuid.uuid4()),
                roles=[customer_role],
                confirmed_at=datetime.utcnow(),
            )
        db.session.commit()

            # Add customer profiles
        customer_profile1 = CustomerProfile(
                user_id=customer1.id,
                address='123 Customer St',
                location_pin_code='123456',
                preferred_services='Plumbing'
            )
        customer_profile2 = CustomerProfile(
                user_id=customer2.id,
                address='456 Client Ave',
                location_pin_code='654321',
                preferred_services='Cleaning'
            )
        db.session.add_all([customer_profile1, customer_profile2])
        db.session.commit()

            # Create professionals
        professional1 = userdatastore.create_user(
                username='pro1',
                email='pro1@example.com',
                phone_number='5555555555',
                password=hash_password('pro1'),
                fs_uniquifier=str(uuid.uuid4()),
                roles=[professional_role],
                confirmed_at=datetime.utcnow(),
            )
        professional2 = userdatastore.create_user(
                username='pro2',
                email='pro2@example.com',
                phone_number='6666666666',
                password=hash_password('pro2'),
                fs_uniquifier=str(uuid.uuid4()),
                roles=[professional_role],
                confirmed_at=datetime.utcnow(),
            )
        db.session.commit()

            # Add professional profiles
        professional_profile1 = Professional(
                user_id=professional1.id,
                service_type='Plumbing',
                experience=5,
                description='Expert in plumbing'
            )
        professional_profile2 = Professional(
                user_id=professional2.id,
                service_type='Cleaning',
                experience=3,
                description='Experienced cleaner'
            )
        db.session.add_all([professional_profile1, professional_profile2])
        db.session.commit()

            # Add services
        plumbing_service = Service(
                name='Plumbing',
                price=100.0,
                time_required=2,
                description='All types of plumbing services'
            )
        cleaning_service = Service(
            name='Cleaning',
            price=50.0,
            time_required=1,
            description='Residential and commercial cleaning services'
        )
        db.session.add_all([plumbing_service, cleaning_service])
        db.session.commit()

        print("Sample data created successfully.")
    else:
        print("Sample users already exist.")
