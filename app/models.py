from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'user', 'volunteer', name='user_roles'), nullable=False)
    pincode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    volunteer_profile = db.relationship('Volunteer', backref='user_profile', uselist=False)
    tasks = db.relationship('Task', backref='task_creator', lazy=True)
    feedback_given = db.relationship('Feedback', foreign_keys='Feedback.user_id', backref='feedback_giver', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skills = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    verification_status = db.Column(db.Enum('pending', 'approved', 'rejected', name='verification_statuses'), default='pending')
    rating = db.Column(db.Float, default=0.0)
    completed_tasks = db.Column(db.Integer, default=0)
    subscription_type = db.Column(db.Enum('basic', 'pro', name='subscription_types'), default='basic')
    subscription_expires = db.Column(db.DateTime)
    premium_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_tasks = db.relationship('Task', backref='assigned_volunteer', lazy=True)
    feedback_received = db.relationship('Feedback', foreign_keys='Feedback.volunteer_id', backref='feedback_receiver', lazy=True)
    
    def __repr__(self):
        return f'<Volunteer {self.user_profile.name}>'

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.Enum('pending', 'assigned', 'completed', 'cancelled', name='task_statuses'), default='pending')
    assigned_volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'))
    is_commercial = db.Column(db.Boolean, default=False)
    payment_amount = db.Column(db.Float, default=0.0)
    platform_fee = db.Column(db.Float, default=0.0)
    urgency = db.Column(db.Enum('low', 'medium', 'high', name='urgency_levels'), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    task_feedback = db.relationship('Feedback', backref='related_task', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    text = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))  # positive, negative, neutral
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback for Task {self.task_id}>'