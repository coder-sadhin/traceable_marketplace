from datetime import datetime
from app import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    product_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50))
    
    # Ownership
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Status
    is_listed = db.Column(db.Boolean, default=False, index=True)
    is_approved = db.Column(db.Boolean, default=False, index=True)
    status = db.Column(db.String(20), default='pending_approval', index=True)
    
    # Pricing
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    original_price = db.Column(db.Numeric(10, 2))
    royalty_percentage = db.Column(db.Numeric(5, 2), default=5.0)
    
    # Condition
    condition = db.Column(db.String(50))
    condition_description = db.Column(db.Text)
    
    # Media
    image_urls = db.Column(db.JSON, default=list)
    digital_file_path = db.Column(db.String(255))
    qr_code_url = db.Column(db.String(255))
    
    # Metadata
    materials = db.Column(db.JSON, default=list)
    dimensions = db.Column(db.String(100))
    weight = db.Column(db.String(50))
    location = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    listed_at = db.Column(db.DateTime)
    sold_at = db.Column(db.DateTime)
    
    # Relationships
    transfers = db.relationship('OwnershipTransfer', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_traceability_url(self):
        from flask import url_for
        return url_for('main.trace_product', product_code=self.unique_code)
    
    def get_ownership_history(self):
        from app.models.ownership_transfer import OwnershipTransfer
        return OwnershipTransfer.query.filter_by(product_id=self.id, status='completed')\
            .order_by(OwnershipTransfer.transfer_date.asc()).all()
    
    def __repr__(self):
        return f'<Product {self.unique_code}: {self.name}>'
