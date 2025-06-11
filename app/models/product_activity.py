from datetime import datetime
from app import db

class ProductActivity(db.Model):
    __tablename__ = 'product_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)  # nullable for non-product activities
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # 'view', 'search', 'transfer', 'admin', 'login', etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # null for anonymous
    ip_address = db.Column(db.String(45))  # IPv6 max length
    user_agent = db.Column(db.String(255))
    activity_data = db.Column(db.JSON, default=dict)  # extra info like search query, transfer details, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    product = db.relationship('Product', backref=db.backref('activities', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProductActivity {self.activity_type}>'


def log_activity(product_id=None, activity_type=None, user_id=None, ip_address=None, 
                  user_agent=None, activity_data=None, request=None):
    """
    Helper function to log activities to the database.
    Can be called from anywhere in the application.
    """
    try:
        activity = ProductActivity(
            product_id=product_id,
            activity_type=activity_type,
            user_id=user_id,
            activity_data=activity_data or {}
        )
        if request:
            activity.ip_address = request.remote_addr
            if request.user_agent:
                activity.user_agent = request.user_agent.string[:255]
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Failed to log activity: {e}")
