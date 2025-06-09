from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.category import Category
from app.models.announcement import Announcement
from app.models.royalty_payment import RoyaltyPayment
from app.models.blockchain_config import BlockchainConfig
from app.models.blockchain_product import BlockchainProduct
from app.models.blockchain_transfer import BlockchainTransfer
from app.models.blockchain_wallet import BlockchainWallet
from app.models.product_activity import ProductActivity, log_activity
from app.blockchain.contract import ProductRegistryContract
from app.blockchain.utils import decrypt_private_key, get_contract_abi
from app.forms.category_forms import CategoryForm
from app.utils.notifications import notify_product_approved, notify_product_rejected, notify_account_suspended
from datetime import datetime
import csv
import io

bp = Blueprint('admin', __name__)

@bp.before_request
@login_required
def check_admin():
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))

# ==================== DASHBOARD ====================
@bp.route('/')
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'listed_products': Product.query.filter_by(is_listed=True).count(),
        'pending_approval': Product.query.filter_by(status='pending_approval').count(),
        'total_transfers': OwnershipTransfer.query.count(),
        'pending_verification': OwnershipTransfer.query.filter_by(status='pending_verification').count(),
        'completed_sales': OwnershipTransfer.query.filter_by(status='completed').count(),
        'total_revenue': db.session.query(db.func.sum(OwnershipTransfer.sale_price)).filter_by(status='completed').scalar() or 0,
        'total_royalties': db.session.query(db.func.sum(OwnershipTransfer.royalty_amount)).filter_by(status='completed').scalar() or 0,
        'total_platform_fees': db.session.query(db.func.sum(OwnershipTransfer.platform_fee)).filter_by(status='completed').scalar() or 0,
        'pending_seller_payouts': OwnershipTransfer.query.filter_by(status='completed', seller_paid=False).count(),
        'total_seller_payouts': db.session.query(db.func.sum(OwnershipTransfer.sale_price)).filter_by(status='completed', seller_paid=True).scalar() or 0
    }
    
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    recent_transfers = OwnershipTransfer.query.order_by(OwnershipTransfer.created_at.desc()).limit(5).all()
    pending_transfers = OwnershipTransfer.query.filter_by(status='pending_verification').order_by(OwnershipTransfer.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_products=recent_products,
                         recent_transfers=recent_transfers,
                         pending_transfers=pending_transfers)

# ==================== USERS ====================
@bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    if search:
        safe_search = search.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{safe_search}%'),
                User.email.ilike(f'%{safe_search}%')
            )
        )
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin' and user.is_active:
        flash('Cannot deactivate the admin user.', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        log_activity(
            activity_type='admin_user_toggle',
            user_id=current_user.id,
            request=request,
            activity_data={'target_user_id': user.id, 'target_username': user.username, 'new_status': status}
        )
        flash(f'User {user.username} {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle user error: {e}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot delete the admin user.', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        log_activity(
            activity_type='admin_user_delete',
            user_id=current_user.id,
            request=request,
            activity_data={'deleted_user_id': user_id, 'deleted_username': user.username}
        )
        flash(f'User {user.username} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete user error: {e}")
        flash('Cannot delete user. They may have existing products or orders.', 'error')
    
    return redirect(url_for('admin.users'))

# ==================== PRODUCTS ====================
@bp.route('/products')
def admin_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Product.query
    if search:
        safe_search = search.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{safe_search}%'),
                Product.unique_code.ilike(f'%{safe_search}%')
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/products.html', products=products)

@bp.route('/products/<int:product_id>/toggle', methods=['POST'])
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        product.is_listed = not product.is_listed
        product.status = 'active' if product.is_listed else 'archived'
        db.session.commit()
        status = 'listed' if product.is_listed else 'unlisted'
        log_activity(
            product_id=product.id,
            activity_type='admin_product_toggle',
            user_id=current_user.id,
            request=request,
            activity_data={'product_code': product.unique_code, 'new_status': status}
        )
        flash(f'Product {product.unique_code} {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle product error: {e}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('admin.admin_products'))

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        log_activity(
            product_id=product_id,
            activity_type='admin_product_delete',
            user_id=current_user.id,
            request=request,
            activity_data={'product_code': product.unique_code, 'product_name': product.name}
        )
        flash(f'Product {product.unique_code} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete product error: {e}")
        flash('Cannot delete product. It may have active orders.', 'error')
    
    return redirect(url_for('admin.admin_products'))

@bp.route('/products/<int:product_id>/logs')
def product_logs(product_id):
    product = Product.query.get_or_404(product_id)
    page = request.args.get('page', 1, type=int)
    activity_type = request.args.get('type', '')
    
    query = ProductActivity.query.filter_by(product_id=product_id)
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    
    activities = query.order_by(ProductActivity.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get stats
    total_views = ProductActivity.query.filter_by(product_id=product_id, activity_type='view').count()
    total_searches = ProductActivity.query.filter_by(product_id=product_id, activity_type='search').count()
    
    return render_template('admin/product_logs.html', 
                           product=product, 
                           activities=activities,
                           total_views=total_views,
                           total_searches=total_searches,
                           activity_type=activity_type)

# ==================== TRANSFERS ====================
@bp.route('/transfers')
def transfers():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = OwnershipTransfer.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    transfers = query.order_by(OwnershipTransfer.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/transfers.html', transfers=transfers)

@bp.route('/transfers/<int:transfer_id>')
def transfer_detail(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    return render_template('admin/transfer_detail.html', transfer=transfer)

@bp.route('/transfers/<int:transfer_id>/resolve', methods=['POST'])
def resolve_transfer(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    action = request.form.get('action')
    
    # Validate status before resolving
    if transfer.status not in ('pending_payment', 'pending_verification'):
        flash(f'This transfer is already {transfer.status.replace("_", " ")}. No action needed.', 'error')
        return redirect(url_for('admin.transfer_detail', transfer_id=transfer.id))
    
    try:
        if action == 'approve':
            transfer.status = 'completed'
            transfer.transfer_date = db.func.now()
            transfer.completed_at = db.func.now()
            
            product = Product.query.get(transfer.product_id)
            product.current_owner_id = transfer.to_user_id
            product.status = 'sold'
            product.is_listed = False
            product.sold_at = datetime.utcnow()
            
            db.session.commit()
            
            try:
                if current_app.config.get('BLOCKCHAIN_ENABLED', True):
                    bc_config = BlockchainConfig.get_active_config()
                    if bc_config and bc_config.is_contract_deployed and product.blockchain_record:
                        from app.models.blockchain_transfer import BlockchainTransfer
                        from app.models.blockchain_wallet import BlockchainWallet
                        from app.blockchain.contract import ProductRegistryContract
                        
                        registry = ProductRegistryContract()
                        if registry.is_ready():
                            from_wallet = BlockchainWallet.query.filter_by(user_id=transfer.from_user_id).first()
                            to_wallet = BlockchainWallet.query.filter_by(user_id=transfer.to_user_id).first()
                            
                            if from_wallet and to_wallet:
                                from app.blockchain.client import BlockchainClient
                                bc_client = BlockchainClient()
                                if not bc_client.is_connected():
                                    raise Exception("Cannot connect to blockchain. Make sure Ganache is running on http://127.0.0.1:8545")
                                ganache_account = bc_client.w3.eth.accounts[0]
                                
                                tx_result = registry.transfer_ownership(
                                    token_id=product.blockchain_record.token_id,
                                    to_address=to_wallet.address,
                                    price=int(float(transfer.sale_price)),
                                    from_address=ganache_account
                                )
                                
                                bc_transfer = BlockchainTransfer(
                                    blockchain_product_id=product.blockchain_record.id,
                                    ownership_transfer_id=transfer.id,
                                    from_address=from_wallet.address,
                                    to_address=to_wallet.address,
                                    transaction_hash=tx_result['transaction_hash'],
                                    block_number=tx_result['block_number'],
                                    gas_used=tx_result['gas_used'],
                                    status='confirmed',
                                    confirmed_at=datetime.utcnow()
                                )
                                db.session.add(bc_transfer)
                                
                                product.blockchain_record.current_owner_address = to_wallet.address
                                db.session.commit()
                                
                                current_app.logger.info(f"Blockchain transfer recorded via admin: {tx_result['transaction_hash']}")
            except Exception as bc_error:
                current_app.logger.error(f"Blockchain transfer error in admin approval: {bc_error}")
            
            flash('Transfer approved and ownership updated.', 'success')
        elif action == 'reject':
            transfer.status = 'rejected'
            transfer.verification_notes = request.form.get('reason', '')
            
            product = Product.query.get(transfer.product_id)
            product.is_listed = True
            product.status = 'active'
            
            flash('Transfer rejected. Product re-listed.', 'info')
        elif action == 'cancel':
            transfer.status = 'cancelled'
            product = Product.query.get(transfer.product_id)
            product.is_listed = True
            product.status = 'active'
            flash('Transfer cancelled.', 'info')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resolve transfer error: {e}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('admin.transfers'))

# ==================== ANALYTICS ====================
@bp.route('/analytics')
def analytics():
    from datetime import datetime
    
    sales_count_label = db.func.count(OwnershipTransfer.id).label('sales_count')
    total_revenue_label = db.func.sum(OwnershipTransfer.sale_price).label('total_revenue')
    top_products = db.session.query(
        Product.name,
        Product.unique_code,
        sales_count_label,
        total_revenue_label
    ).join(OwnershipTransfer, Product.id == OwnershipTransfer.product_id)\
     .filter(OwnershipTransfer.status == 'completed')\
     .group_by(Product.id)\
     .order_by(sales_count_label.desc())\
     .limit(10).all()

    total_royalty_label = db.func.sum(OwnershipTransfer.royalty_amount).label('total_royalty')
    top_creators = db.session.query(
        User.username,
        total_royalty_label
    ).join(Product, User.id == Product.creator_id)\
     .join(OwnershipTransfer, Product.id == OwnershipTransfer.product_id)\
     .filter(OwnershipTransfer.status == 'completed')\
     .group_by(User.id)\
     .order_by(total_royalty_label.desc())\
     .limit(10).all()
    
    return render_template('admin/analytics.html', 
                         top_products=top_products,
                         top_creators=top_creators)

# ==================== CATEGORIES ====================
@bp.route('/categories')
def categories():
    categories = Category.query.order_by(Category.name).all()
    form = CategoryForm()
    return render_template('admin/categories.html', categories=categories, form=form)

@bp.route('/categories/create', methods=['POST'])
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = Category(
                name=form.name.data,
                slug=form.slug.data,
                description=form.description.data,
                is_active=form.is_active.data
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{category.name}" created.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Category creation failed. Name or slug may already exist.', 'error')
    return redirect(url_for('admin.categories'))

@bp.route('/categories/<int:category_id>/edit', methods=['POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.slug = form.slug.data
            category.description = form.description.data
            category.is_active = form.is_active.data
            db.session.commit()
            flash(f'Category "{category.name}" updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Update failed. Name or slug may already exist.', 'error')
    return redirect(url_for('admin.categories'))

@bp.route('/categories/<int:category_id>/toggle', methods=['POST'])
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        category.is_active = not category.is_active
        db.session.commit()
        status = 'activated' if category.is_active else 'deactivated'
        flash(f'Category "{category.name}" {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.categories'))

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    product_count = category.product_count()
    if product_count > 0:
        flash(f'Cannot delete "{category.name}" — it has {product_count} products.', 'error')
        return redirect(url_for('admin.categories'))
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.categories'))

# ==================== ROLE MANAGEMENT ====================
@bp.route('/users/<int:user_id>/role', methods=['POST'])
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot change your own role.', 'error')
        return redirect(url_for('admin.users'))
    
    new_role = request.form.get('role', 'user')
    valid_roles = ['user', 'admin', 'moderator']
    if new_role not in valid_roles:
        flash('Invalid role.', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        user.role = new_role
        db.session.commit()
        flash(f'{user.username} role changed to {new_role}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.users'))

# ==================== SELLER PAYOUTS ====================
@bp.route('/seller-payouts')
def seller_payouts():
    """List completed transfers where seller hasn't been paid yet."""
    transfers = OwnershipTransfer.query.filter_by(status='completed', seller_paid=False)\
        .order_by(OwnershipTransfer.completed_at.desc()).all()
    total_pending = db.session.query(db.func.sum(OwnershipTransfer.sale_price))\
        .filter_by(status='completed', seller_paid=False).scalar() or 0
    return render_template('admin/seller_payouts.html', transfers=transfers, total_pending=total_pending)

@bp.route('/seller-payouts/<int:transfer_id>/pay', methods=['POST'])
def pay_seller(transfer_id):
    """Mark a seller as paid for a completed transfer."""
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    if transfer.status != 'completed':
        flash('Transfer must be completed before paying seller.', 'error')
        return redirect(url_for('admin.seller_payouts'))
    try:
        transfer.seller_paid = True
        transfer.seller_paid_at = db.func.now()
        transfer.seller_paid_notes = request.form.get('notes', '')
        db.session.commit()
        # Notify seller they've been paid
        from app.utils.notifications import create_notification
        create_notification(
            user_id=transfer.from_user_id,
            title='Payment Received',
            message=f'You have been paid ¥{transfer.seller_receives():.2f} for "{transfer.product.name}". The platform has processed your payout.',
            notification_type='success',
            related_type='transfer',
            related_id=transfer.id
        )
        flash(f'Seller {transfer.from_user.username} marked as paid. Amount: ¥{transfer.seller_receives():.2f}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.seller_payouts'))

# ==================== PAYOUT MANAGEMENT ====================
@bp.route('/payouts')
def payouts():
    from app.models.royalty_payment import RoyaltyPayment
    from app.models.user import User as UserModel
    
    payouts = RoyaltyPayment.query.order_by(RoyaltyPayment.created_at.desc()).all()
    total_pending = db.session.query(db.func.sum(RoyaltyPayment.amount)).filter_by(status='pending').scalar() or 0
    total_paid = db.session.query(db.func.sum(RoyaltyPayment.amount)).filter_by(status='paid').scalar() or 0
    
    return render_template('admin/payouts.html', 
                         payouts=payouts, 
                         total_pending=total_pending, 
                         total_paid=total_paid)

@bp.route('/payouts/<int:payout_id>/mark-paid', methods=['POST'])
def mark_payout_paid(payout_id):
    from app.models.royalty_payment import RoyaltyPayment
    
    payout = RoyaltyPayment.query.get_or_404(payout_id)
    try:
        payout.status = 'paid'
        payout.paid_at = db.func.now()
        db.session.commit()
        flash(f'Payout #{payout.id} marked as paid.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.payouts'))

# ==================== PRODUCT APPROVAL ====================
@bp.route('/pending-products')
def pending_products():
    products = Product.query.filter_by(status='pending_approval').order_by(Product.created_at.desc()).all()
    return render_template('admin/pending_products.html', products=products)

@bp.route('/products/<int:product_id>/approve', methods=['POST'])
def approve_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        product.is_approved = True
        product.is_listed = True
        product.status = 'active'
        product.listed_at = db.func.now()
        db.session.commit()
        
        # Log product approval
        log_activity(
            product_id=product.id,
            activity_type='admin_product_approve',
            user_id=current_user.id,
            request=request,
            activity_data={'product_code': product.unique_code, 'product_name': product.name}
        )
        
        # Blockchain: Mint product on blockchain when approved
        try:
            if current_app.config.get('BLOCKCHAIN_ENABLED', True):
                bc_config = BlockchainConfig.get_active_config()
                if bc_config and bc_config.is_contract_deployed:
                    registry = ProductRegistryContract()
                    if registry.is_ready():
                        # Get or create wallet for creator
                        creator_wallet = BlockchainWallet.query.filter_by(user_id=product.creator_id).first()
                        if not creator_wallet:
                            from app.blockchain.utils import generate_wallet, encrypt_private_key
                            wallet_data = generate_wallet()
                            creator_wallet = BlockchainWallet(
                                user_id=product.creator_id,
                                address=wallet_data['address'],
                                private_key_encrypted=encrypt_private_key(wallet_data['private_key'])
                            )
                            db.session.add(creator_wallet)
                            db.session.commit()
                        
                        # Mint product on blockchain using Ganache account 0 (unlocked)
                        from app.blockchain.client import BlockchainClient
                        bc_client = BlockchainClient()
                        if not bc_client.is_connected():
                            raise Exception("Cannot connect to blockchain. Make sure Ganache is running on http://127.0.0.1:8545")
                        ganache_account = bc_client.w3.eth.accounts[0]
                        
                        tx_result = registry.mint_product(
                            product_code=product.unique_code,
                            metadata_uri=f"http://localhost:5000/trace/{product.unique_code}",
                            creator_address=creator_wallet.address,
                            from_address=ganache_account
                        )
                        
                        # Create blockchain product record
                        bc_product = BlockchainProduct(
                            product_id=product.id,
                            token_id=tx_result.get('token_id', 0),
                            contract_address=bc_config.contract_address,
                            network=bc_config.network,
                            metadata_uri=f"http://localhost:5000/trace/{product.unique_code}",
                            transaction_hash=tx_result['transaction_hash'],
                            block_number=tx_result['block_number'],
                            is_minted=True,
                            minted_at=datetime.utcnow(),
                            current_owner_address=creator_wallet.address
                        )
                        db.session.add(bc_product)
                        db.session.commit()
                        
                        current_app.logger.info(f"Product minted on blockchain: {product.unique_code} token={tx_result.get('token_id', 0)}")
        except Exception as bc_error:
            current_app.logger.error(f"Blockchain minting error: {bc_error}")
            flash(f'Product approved but blockchain minting failed: {str(bc_error)}', 'warning')
        
        notify_product_approved(
            creator_id=product.creator_id,
            product_name=product.name,
            product_code=product.unique_code
        )
        
        flash(f'Product "{product.name}" approved and listed.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Approve product error: {e}")
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.pending_products'))

@bp.route('/products/<int:product_id>/mint', methods=['POST'])
def mint_product(product_id):
    """Manually mint an existing approved product on blockchain."""
    product = Product.query.get_or_404(product_id)
    
    # Check if already minted
    existing_bc = BlockchainProduct.query.filter_by(product_id=product.id).first()
    if existing_bc and existing_bc.is_minted:
        flash('Product already minted on blockchain.', 'info')
        return redirect(url_for('admin.admin_products'))
    
    try:
        bc_config = BlockchainConfig.get_active_config()
        if not bc_config or not bc_config.is_contract_deployed:
            flash('Contract not deployed. Deploy it first.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        registry = ProductRegistryContract()
        if not registry.is_ready():
            flash('Blockchain not connected. Make sure Ganache is running.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        # Get or create wallet for creator
        creator_wallet = BlockchainWallet.query.filter_by(user_id=product.creator_id).first()
        if not creator_wallet:
            from app.blockchain.utils import generate_wallet, encrypt_private_key
            wallet_data = generate_wallet()
            creator_wallet = BlockchainWallet(
                user_id=product.creator_id,
                address=wallet_data['address'],
                private_key_encrypted=encrypt_private_key(wallet_data['private_key'])
            )
            db.session.add(creator_wallet)
            db.session.commit()
        
        # Mint using Ganache account 0
        from app.blockchain.client import BlockchainClient
        bc_client = BlockchainClient()
        if not bc_client.is_connected():
            flash('Cannot connect to blockchain. Make sure Ganache is running on http://127.0.0.1:8545', 'error')
            return redirect(url_for('admin.admin_products'))
        ganache_account = bc_client.w3.eth.accounts[0]
        
        tx_result = registry.mint_product(
            product_code=product.unique_code,
            metadata_uri=f"http://localhost:5000/trace/{product.unique_code}",
            creator_address=creator_wallet.address,
            from_address=ganache_account
        )
        
        # Create blockchain product record
        bc_product = BlockchainProduct(
            product_id=product.id,
            token_id=tx_result.get('token_id', 0),
            contract_address=bc_config.contract_address,
            network=bc_config.network,
            metadata_uri=f"http://localhost:5000/trace/{product.unique_code}",
            transaction_hash=tx_result['transaction_hash'],
            block_number=tx_result['block_number'],
            is_minted=True,
            minted_at=datetime.utcnow(),
            current_owner_address=creator_wallet.address
        )
        db.session.add(bc_product)
        db.session.commit()
        
        flash(f'Product "{product.name}" minted on blockchain! Token ID: {tx_result.get("token_id", 0)}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mint product error: {e}")
        flash(f'Minting failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_products'))

@bp.route('/products/<int:product_id>/reject', methods=['POST'])
def reject_product(product_id):
    product = Product.query.get_or_404(product_id)
    reason = request.form.get('reason', 'Does not meet platform standards.')
    try:
        product.is_approved = False
        product.is_listed = False
        product.status = 'rejected'
        db.session.commit()
        
        log_activity(
            product_id=product.id,
            activity_type='admin_product_reject',
            user_id=current_user.id,
            request=request,
            activity_data={'product_code': product.unique_code, 'product_name': product.name, 'reason': reason}
        )
        
        notify_product_rejected(
            creator_id=product.creator_id,
            product_name=product.name,
            reason=reason
        )
        
        flash(f'Product "{product.name}" rejected. Reason: {reason}', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.pending_products'))

# ==================== USER SUSPENSION ====================
@bp.route('/users/<int:user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash('Cannot suspend admin.', 'error')
        return redirect(url_for('admin.users'))
    
    duration = request.form.get('duration', '7')  # days
    reason = request.form.get('reason', 'Violation of platform rules.')
    
    try:
        from datetime import datetime, timedelta
        suspend_until = datetime.utcnow() + timedelta(days=int(duration))
        user.suspended_until = suspend_until
        user.suspension_reason = reason
        db.session.commit()
        
        log_activity(
            activity_type='admin_user_suspend',
            user_id=current_user.id,
            request=request,
            activity_data={'target_user_id': user.id, 'target_username': user.username, 'duration': duration, 'reason': reason}
        )
        
        notify_account_suspended(
            user_id=user.id,
            reason=reason,
            end_date=suspend_until.strftime('%Y-%m-%d')
        )
        
        flash(f'{user.username} suspended for {duration} days.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/unsuspend', methods=['POST'])
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.suspended_until = None
        user.suspension_reason = None
        db.session.commit()
        log_activity(
            activity_type='admin_user_unsuspend',
            user_id=current_user.id,
            request=request,
            activity_data={'target_user_id': user.id, 'target_username': user.username}
        )
        flash(f'{user.username} suspension lifted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/verify', methods=['POST'])
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.is_verified = True
        user.verified_at = db.func.now()
        user.verification_token = None
        db.session.commit()
        log_activity(
            activity_type='admin_user_verify',
            user_id=current_user.id,
            request=request,
            activity_data={'target_user_id': user.id, 'target_username': user.username}
        )
        flash(f'{user.username} email verified by admin.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.users'))

# ==================== ANNOUNCEMENTS ====================
@bp.route('/announcements')
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)

@bp.route('/announcements/create', methods=['POST'])
def create_announcement():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    announcement_type = request.form.get('announcement_type', 'info')

    if not title or not content:
        flash('Title and content are required.', 'error')
        return redirect(url_for('admin.announcements'))

    try:
        announcement = Announcement(
            title=title,
            content=content,
            announcement_type=announcement_type,
            is_active=True,
            created_by=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create announcement error: {e}")
        flash('An error occurred.', 'error')

    return redirect(url_for('admin.announcements'))

@bp.route('/announcements/<int:announcement_id>/toggle', methods=['POST'])
def toggle_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        announcement.is_active = not announcement.is_active
        db.session.commit()
        status = 'activated' if announcement.is_active else 'deactivated'
        flash(f'Announcement "{announcement.title}" {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.announcements'))

@bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash(f'Announcement "{announcement.title}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('admin.announcements'))

# ==================== CSV EXPORTS ====================
@bp.route('/export/sales-csv')
def export_sales_csv():
    transfers = OwnershipTransfer.query.filter_by(status='completed').order_by(OwnershipTransfer.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Product', 'Product Code', 'Seller', 'Buyer', 'Sale Price',
                     'Royalty Amount', 'Platform Fee', 'Status', 'Transfer Date', 'Created At'])

    for t in transfers:
        writer.writerow([
            t.id,
            t.product.name if t.product else '',
            t.product.unique_code if t.product else '',
            t.from_user.username if t.from_user else '',
            t.to_user.username if t.to_user else '',
            float(t.sale_price or 0),
            float(t.royalty_amount or 0),
            float(t.platform_fee or 0),
            t.status,
            t.transfer_date.strftime('%Y-%m-%d %H:%M:%S') if t.transfer_date else '',
            t.created_at.strftime('%Y-%m-%d %H:%M:%S') if t.created_at else ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=sales_report.csv'
    return response

@bp.route('/export/payouts-csv')
def export_payouts_csv():
    payouts = RoyaltyPayment.query.order_by(RoyaltyPayment.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Creator', 'Transfer ID', 'Amount', 'Status', 'Payment Method',
                     'Reference', 'Paid At', 'Created At'])

    for p in payouts:
        writer.writerow([
            p.id,
            p.creator.username if p.creator else '',
            p.transfer_id,
            float(p.amount or 0),
            p.status,
            p.payment_method or '',
            p.reference or '',
            p.paid_at.strftime('%Y-%m-%d %H:%M:%S') if p.paid_at else '',
            p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=payouts_report.csv'
    return response

@bp.route('/export/users-csv')
def export_users_csv():
    users = User.query.order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Active', 'Verified',
                     'Created At', 'Last Login'])

    for u in users:
        writer.writerow([
            u.id,
            u.username,
            u.email,
            u.role,
            u.is_active,
            u.is_verified,
            u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else '',
            u.last_login.strftime('%Y-%m-%d %H:%M:%S') if u.last_login else ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=users_report.csv'
    return response

@bp.route('/reports')
def reports():
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'completed_sales': OwnershipTransfer.query.filter_by(status='completed').count(),
        'total_revenue': db.session.query(db.func.sum(OwnershipTransfer.sale_price)).filter_by(status='completed').scalar() or 0,
    }
    return render_template('admin/reports.html', stats=stats)

# ==================== ADMIN SETTINGS ====================
@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        try:
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = current_user
            
            # Payment QR Code Upload
            if 'payment_qr' in request.files:
                qr_file = request.files['payment_qr']
                if qr_file and qr_file.filename:
                    from app.utils.file_validator import secure_save_file, allowed_image
                    if allowed_image(qr_file.filename):
                        qr_path = secure_save_file(qr_file, 'qr_codes')
                        admin.payment_qr_url = qr_path
                        flash('QR code uploaded!', 'success')
                    else:
                        flash('Invalid image format. Use JPG, PNG, or GIF.', 'error')
            
            # Bank Details
            admin.bank_details = request.form.get('bank_details', '').strip() or None
            
            # Platform Settings
            platform_fee_percent = request.form.get('platform_fee_percent', '3')
            try:
                current_app.config['PLATFORM_FEE_PERCENT'] = float(platform_fee_percent)
            except ValueError:
                pass
            
            db.session.commit()
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving settings.', 'error')
        return redirect(url_for('admin.settings'))
    
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = current_user
    
    platform_fee = current_app.config.get('PLATFORM_FEE_PERCENT', 3)
    
    return render_template('admin/settings.html', admin=admin, platform_fee=platform_fee)

# ==================== BLOCKCHAIN ====================
@bp.route('/blockchain')
def blockchain_status():
    from app.blockchain.client import BlockchainClient
    from app.blockchain.utils import generate_wallet, encrypt_private_key
    
    client = BlockchainClient()
    connected = client.is_connected()
    block_number = client.get_block_number() if connected else 0
    
    bc_config = BlockchainConfig.get_active_config()
    contract = ProductRegistryContract()
    
    stats = {
        'connected': connected,
        'block_number': block_number,
        'network': bc_config.network if bc_config else 'ganache',
        'rpc_url': bc_config.rpc_url if bc_config else 'http://127.0.0.1:8545',
        'contract_deployed': bc_config.is_contract_deployed if bc_config else False,
        'contract_address': bc_config.contract_address if bc_config else None,
        'total_minted': BlockchainProduct.query.count(),
        'total_transfers': BlockchainTransfer.query.count(),
        'total_wallets': BlockchainWallet.query.count()
    }
    
    recent_mints = BlockchainProduct.query.order_by(BlockchainProduct.created_at.desc()).limit(10).all()
    recent_transfers = BlockchainTransfer.query.order_by(BlockchainTransfer.created_at.desc()).limit(10).all()
    
    return render_template('admin/blockchain.html',
                         stats=stats,
                         recent_mints=recent_mints,
                         recent_transfers=recent_transfers,
                         bc_config=bc_config)

@bp.route('/blockchain/deploy', methods=['POST'])
def deploy_contract():
    from app.blockchain.client import BlockchainClient
    from app.blockchain.contract import ProductRegistryContract
    from app.blockchain.utils import encrypt_private_key
    
    try:
        # Check if already deployed
        existing = BlockchainConfig.get_active_config()
        if existing and existing.is_contract_deployed:
            flash('Contract already deployed.', 'info')
            return redirect(url_for('admin.blockchain_status'))
        
        client = BlockchainClient()
        if not client.is_connected():
            flash('Cannot connect to blockchain. Make sure Ganache is running.', 'error')
            return redirect(url_for('admin.blockchain_status'))
        
        # Use first Ganache account (pre-unlocked, no signing needed)
        accounts = client.w3.eth.accounts
        if not accounts:
            flash('No accounts available on Ganache.', 'error')
            return redirect(url_for('admin.blockchain_status'))
        
        platform_address = accounts[0]
        
        # Deploy using transact() - Ganache accounts are unlocked
        contract_wrapper = ProductRegistryContract()
        result = contract_wrapper.deploy(platform_address)
        
        # Save config
        if existing:
            bc_config = existing
        else:
            bc_config = BlockchainConfig()
        
        bc_config.network = 'ganache'
        bc_config.rpc_url = current_app.config.get('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:8545')
        bc_config.chain_id = current_app.config.get('BLOCKCHAIN_CHAIN_ID', 1337)
        bc_config.contract_address = result['contract_address']
        bc_config.contract_abi = get_contract_abi()
        bc_config.deployed_at = datetime.utcnow()
        bc_config.deployer_address = platform_address
        bc_config.platform_address = platform_address
        bc_config.platform_private_key = ''
        bc_config.is_active = True
        bc_config.is_contract_deployed = True
        
        db.session.add(bc_config)
        db.session.commit()
        
        flash(f'Contract deployed successfully at {result["contract_address"]}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Deploy contract error: {e}")
        flash(f'Deployment failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.blockchain_status'))

@bp.route('/blockchain/setup-wallets', methods=['POST'])
def setup_user_wallets():
    """Generate blockchain wallets for all existing users."""
    from app.blockchain.utils import generate_wallet, encrypt_private_key
    
    try:
        users = User.query.all()
        created = 0
        for user in users:
            existing = BlockchainWallet.query.filter_by(user_id=user.id).first()
            if not existing:
                wallet_data = generate_wallet()
                wallet = BlockchainWallet(
                    user_id=user.id,
                    address=wallet_data['address'],
                    private_key_encrypted=encrypt_private_key(wallet_data['private_key'])
                )
                db.session.add(wallet)
                created += 1
        
        db.session.commit()
        flash(f'Created {created} blockchain wallets for users.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Setup wallets error: {e}")
        flash(f'Failed to setup wallets: {str(e)}', 'error')
    
    return redirect(url_for('admin.blockchain_status'))
