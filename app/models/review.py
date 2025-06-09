from datetime import datetime
from app import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')
    product = db.relationship('Product', backref='reviews')

    __table_args__ = (db.UniqueConstraint('product_id', 'user_id', name='unique_review'),)

    def __repr__(self):
        return f'<Review {self.id} by User {self.user_id}>'
