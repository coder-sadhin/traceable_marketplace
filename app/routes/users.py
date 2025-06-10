from flask import Blueprint, render_template, abort
from app.models.user import User
from app.models.product import Product

bp = Blueprint('users', __name__)

@bp.route('/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not user.is_active:
        abort(404)
    products = Product.query.filter_by(creator_id=user.id, is_listed=True, is_approved=True).order_by(Product.created_at.desc()).all()
    total_sales = user.transfers_from.filter_by(status='completed').count()
    stats = {
        'products_created': len(products),
        'sales_count': total_sales
    }
    return render_template('users/public_profile.html', user=user, products=products, stats=stats)
