from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    
    # Verification
    is_verified = db.Column(db.Boolean, default=True)
    verification_token = db.Column(db.String(100), unique=True)
    verified_at = db.Column(db.DateTime)
    
    # Suspension
    suspended_until = db.Column(db.DateTime)
    suspension_reason = db.Column(db.Text)
    
    # Payment info
    payment_qr_url = db.Column(db.String(255))
    bank_details = db.Column(db.Text)
    
    # Profile
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_products = db.relationship('Product', foreign_keys='Product.creator_id', backref='creator', lazy='dynamic')
    owned_products = db.relationship('Product', foreign_keys='Product.current_owner_id', backref='current_owner', lazy='dynamic')
    transfers_from = db.relationship('OwnershipTransfer', foreign_keys='OwnershipTransfer.from_user_id', backref='from_user', lazy='dynamic')
    transfers_to = db.relationship('OwnershipTransfer', foreign_keys='OwnershipTransfer.to_user_id', backref='to_user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_suspended(self):
        if not self.suspended_until:
            return False
        return self.suspended_until > datetime.utcnow()
    
    def generate_verification_token(self):
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
