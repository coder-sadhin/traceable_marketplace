from flask import Blueprint, render_template
from app import db
from app.models.product import Product
from app.models.product_activity import ProductActivity
from sqlalchemy import func

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get products ordered by activity count (most viewed first), limit 12
    featured = db.session.query(
        Product,
        func.count(ProductActivity.id).label('activity_count')
    ).outerjoin(
        ProductActivity, Product.id == ProductActivity.product_id
    ).filter(
        Product.is_listed == True,
        Product.is_approved == True
    ).group_by(
        Product.id
    ).order_by(
        func.count(ProductActivity.id).desc()
    ).limit(12).all()
    
    # featured is a list of tuples (Product, activity_count), extract products
    featured = [p[0] for p in featured]
    
    return render_template('main/index.html', featured=featured)

@bp.route('/trace/<product_code>')
def trace_product(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    history = product.get_ownership_history()
    return render_template('main/trace.html', product=product, history=history)
