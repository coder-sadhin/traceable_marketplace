from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def product_count(self):
        from app.models.product import Product
        return Product.query.filter_by(category=self.name, is_listed=True).count()

    def __repr__(self):
        return f'<Category {self.name}>'
