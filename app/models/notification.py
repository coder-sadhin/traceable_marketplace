from datetime import datetime
from app import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, success, warning, error
    
    # Link to related object
    related_type = db.Column(db.String(50))  # 'product', 'order', 'transfer'
    related_id = db.Column(db.Integer)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref='notifications')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
