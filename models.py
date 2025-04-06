from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import backref,relationship
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(50), nullable=False)

    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)
    services = db.relationship('Service', backref='customer', lazy=True)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    license_plate = db.Column(db.String(20), unique=True)
    vin = db.Column(db.String(17), unique=True)
    odo_reading = db.Column(db.Integer)
    last_service_date = db.Column(db.DateTime)
    next_service_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    services = db.relationship('Service', backref='vehicle', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50))
    scheduled_date = db.Column(db.DateTime)
    actual_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in-progress, completed, cancelled
    cost = db.Column(db.Float)
    odometer_reading = db.Column(db.Integer)
    notes = db.Column(db.Text)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    history = db.relationship('ServiceHistory', backref='service', lazy=True)
    payment = db.relationship('Payment', backref='service', uselist=False)
    user = db.relationship('User', backref='user_services', lazy=True)

class ServiceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    amount = db.Column(db.Float)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    transaction_id = db.Column(db.String(100))

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def is_admin(self):
        return True

    def __repr__(self):
        return f"Admin('{self.name}', '{self.email}')"
