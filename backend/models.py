from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask_security import UserMixin, RoleMixin
from flask import Flask
from sqlalchemy.orm import relationship

import uuid

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)
    roles = db.relationship('Role', secondary='user_roles', backref='bearers')
    customer = db.relationship('CustomerProfile', back_populates='user', uselist=False)


    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "phone_number": self.phone_number,
            "email": self.email,
            "active": self.active,
            "roles": [role.name for role in self.roles],
        }

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id =db.Column(db.Integer, db.ForeignKey('roles.id'))
    
class CustomerProfile(db.Model):
    __tablename__ = 'customer_profile'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address = db.Column(db.Text)
    location_pin_code = db.Column(db.String(10))
    blocked = db.Column(db.Boolean, default=False)
    preferred_services = db.Column(db.Text)

    user = db.relationship('User', backref='customers', lazy=True)
        
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "address": self.address,
            "location_pin_code": self.location_pin_code,
            "blocked": self.blocked,
            "preferred_services": self.preferred_services,
        }

class Professional(db.Model):
    __tablename__ = 'professional'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_type = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer)
    description = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    experience_proof = db.Column(db.String(255))
    
    user = db.relationship('User', backref='professionals', lazy=True)


    @property
    def average_rating(self):
        reviews = Review.query.filter_by(reviewee_id=self.user_id).all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            return round(total_rating / len(reviews), 2)
        return None

    def to_dict(self):
        completed_requests = ServiceRequest.query.filter_by(professional_id=self.user_id, service_status="Closed").all()
        remarks = [request.remarks for request in completed_requests if request.remarks]
        return {
            "id": self.id,
            "user_id": self.user_id,
            "service_type": self.service_type,
            "experience": self.experience,
            "description": self.description,
            "verified": self.verified,
            "blocked": self.blocked,
            "average_rating": self.average_rating,
            "remarks": remarks,  # Adding remarks
        }


class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    time_required = db.Column(db.Integer)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "time_required": self.time_required,
            "description": self.description,
        }


class ServiceRequest(db.Model):
    __tablename__ = 'service_request'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow)
    service_status = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    date_closed = db.Column(db.DateTime)

    # Relationships
    service = db.relationship('Service', backref='requests')
    professional = db.relationship('User', foreign_keys=[professional_id])  # Add this line
    reviews = db.relationship('Review', back_populates='service_request', lazy=True)

    def to_dict(self):
        def format_datetime(dt):
            return dt.isoformat() if dt else None
        return {
            "id": self.id,
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "professional_id": self.professional_id,
            "professional_name": self.professional.username, 
            "pro_phone_no" : self.professional.phone_number,
            "date_of_request": self.date_of_request,
            "service_status": self.service_status,
            "remarks": self.remarks,
            "date_closed": self.date_closed,
        }


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    service_request = db.relationship('ServiceRequest', back_populates='reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    reviewee = db.relationship('User', foreign_keys=[reviewee_id])

    def to_dict(self):
        return {
            "id": self.id,
            "service_request_id": self.service_request_id,
            "reviewer_id": self.reviewer_id,
            "reviewee_id": self.reviewee_id,
            "rating": self.rating,
            "review": self.review,
            "timestamp": self.timestamp,
        }


class Block(db.Model):
    __tablename__ = 'block'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    blocked_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blocked_user = db.relationship('User', foreign_keys=[blocked_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "blocked_user_id": self.blocked_user_id,
        }
