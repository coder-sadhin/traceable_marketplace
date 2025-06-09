from datetime import datetime
from app import db

class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='wishlist_items')
    product = db.relationship('Product', backref='wishlist_entries')

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_user_product_wishlist'),)

    def __repr__(self):
        return f'<Wishlist {self.user_id}: Product {self.product_id}>'
