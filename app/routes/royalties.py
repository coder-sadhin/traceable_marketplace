from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.royalty_payment import RoyaltyPayment

bp = Blueprint('royalties', __name__)

@bp.route('/')
@login_required
def dashboard():
    # Get all products created by this user
    products = Product.query.filter_by(creator_id=current_user.id).all()
    product_ids = [p.id for p in products]

    # Get all completed transfers (resales) of user's products
    transfers = OwnershipTransfer.query.filter(
        OwnershipTransfer.product_id.in_(product_ids),
        OwnershipTransfer.status == 'completed'
    ).order_by(OwnershipTransfer.transfer_date.desc()).all()

    # Get royalty payments
    payments = RoyaltyPayment.query.filter_by(creator_id=current_user.id).order_by(RoyaltyPayment.created_at.desc()).all()

    # Calculate totals
    total_earned = sum(t.royalty_amount for t in transfers)
    total_paid = sum(p.amount for p in payments if p.status == 'paid')
    total_pending = sum(p.amount for p in payments if p.status == 'pending')

    return render_template('royalties/dashboard.html',
                         transfers=transfers,
                         payments=payments,
                         total_earned=total_earned,
                         total_paid=total_paid,
                         total_pending=total_pending)
