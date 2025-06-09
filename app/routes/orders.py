from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.user import User
from app.models.blockchain_config import BlockchainConfig
from app.models.blockchain_transfer import BlockchainTransfer
from app.models.blockchain_wallet import BlockchainWallet
from app.models.product_activity import log_activity
from app.blockchain.contract import ProductRegistryContract
from app.blockchain.utils import decrypt_private_key
from app.utils.file_validator import secure_save_file, allowed_image
from app.utils.notifications import (
    notify_product_sold, notify_receipt_uploaded,
    notify_payment_verified, notify_payment_rejected
)
from datetime import datetime, timedelta

bp = Blueprint('orders', __name__)

@bp.route('/checkout/<product_code>')
@login_required
def checkout(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    if not product.is_approved or not product.is_listed:
        flash('This product is not available for purchase.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    if product.current_owner_id == current_user.id:
        flash('You cannot buy your own product.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    seller = User.query.get(product.current_owner_id)
    royalty_amount = float(product.current_price) * float(product.royalty_percentage) / 100
    platform_fee_percent = current_app.config.get('PLATFORM_FEE_PERCENT', 3)
    platform_fee = float(product.current_price) * platform_fee_percent / 100
    
    # Get admin user for payment info (all payments go to admin)
    admin = User.query.filter_by(role='admin').first()
    
    # Log checkout view
    log_activity(
        product_id=product.id,
        activity_type='checkout_view',
        user_id=current_user.id,
        request=request,
        activity_data={'product_code': product_code, 'price': str(product.current_price)}
    )
    
    return render_template('orders/checkout.html', 
                         product=product, 
                         seller=seller, 
                         admin=admin,
                         royalty_amount=royalty_amount,
                         platform_fee=platform_fee)

@bp.route('/checkout/<product_code>/confirm', methods=['POST'])
@login_required
def confirm_checkout(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    if not product.is_approved or not product.is_listed:
        flash('This product is not available for purchase.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))

    if product.current_owner_id == current_user.id:
        flash('You cannot buy your own product.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    try:
        # Lock the product
        product.is_listed = False
        product.status = 'pending_sale'
        
        # Create ownership transfer record
        platform_fee_percent = current_app.config.get('PLATFORM_FEE_PERCENT', 3)
        platform_fee = float(product.current_price) * platform_fee_percent / 100
        transfer = OwnershipTransfer(
            product_id=product.id,
            from_user_id=product.current_owner_id,
            to_user_id=current_user.id,
            sale_price=product.current_price,
            royalty_percentage=product.royalty_percentage,
            royalty_amount=float(product.current_price) * float(product.royalty_percentage) / 100,
            platform_fee=platform_fee,
            platform_fee_percentage=platform_fee_percent,
            status='pending_payment'
        )
        
        db.session.add(transfer)
        db.session.commit()
        
        # Log transfer initiated
        log_activity(
            product_id=product.id,
            activity_type='transfer_initiated',
            user_id=current_user.id,
            request=request,
            activity_data={
                'transfer_id': transfer.id,
                'product_code': product_code,
                'from_user_id': product.current_owner_id,
                'to_user_id': current_user.id,
                'price': str(product.current_price)
            }
        )
        
        # Notify seller
        seller = User.query.get(product.current_owner_id)
        notify_product_sold(
            seller_id=seller.id,
            product_name=product.name,
            buyer_username=current_user.username,
            price=float(product.current_price)
        )
        
        flash('Please complete the payment and upload your receipt.', 'info')
        return redirect(url_for('orders.upload_receipt', transfer_id=transfer.id))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Checkout error: {e}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))

@bp.route('/upload-receipt/<int:transfer_id>', methods=['GET', 'POST'])
@login_required
def upload_receipt(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    
    if transfer.to_user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Only allow upload if transfer is pending payment
    if transfer.status != 'pending_payment':
        flash(f'This order is already {transfer.status.replace("_", " ")}.', 'error')
        return redirect(url_for('orders.my_orders'))
    
    if request.method == 'POST':
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_image(file.filename):
                receipt_url = secure_save_file(file, 'receipts', prefix='receipt_')
                if receipt_url:
                    try:
                        transfer.payment_receipt_url = receipt_url
                        transfer.status = 'pending_verification'
                        db.session.commit()
                        
                        # Log receipt upload
                        log_activity(
                            product_id=transfer.product_id,
                            activity_type='receipt_uploaded',
                            user_id=current_user.id,
                            request=request,
                            activity_data={
                                'transfer_id': transfer.id,
                                'receipt_url': receipt_url
                            }
                        )
                        
                        # Notify seller that receipt was uploaded
                        product = Product.query.get(transfer.product_id)
                        seller = User.query.get(transfer.from_user_id)
                        notify_receipt_uploaded(
                            seller_id=seller.id,
                            product_name=product.name,
                            buyer_username=current_user.username
                        )
                        
                        flash('Receipt uploaded! Seller will verify your payment.', 'success')
                        return redirect(url_for('orders.my_orders'))
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"Receipt upload error: {e}")
                        flash('An error occurred. Please try again.', 'error')
        
        flash('Please upload a valid receipt image.', 'error')
    
    product = Product.query.get(transfer.product_id)
    seller = User.query.get(transfer.from_user_id)
    
    return render_template('orders/upload_receipt.html', 
                         transfer=transfer, 
                         product=product, 
                         seller=seller)

@bp.route('/verify-receipt/<int:transfer_id>', methods=['GET', 'POST'])
@login_required
def verify_receipt(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    
    if transfer.from_user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Only allow verify if transfer is pending verification
    if transfer.status != 'pending_verification':
        flash(f'This order is already {transfer.status.replace("_", " ")}.', 'error')
        return redirect(url_for('orders.my_sales'))
    
    product = Product.query.get(transfer.product_id)
    buyer = User.query.get(transfer.to_user_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approve':
            try:
                # Complete the transfer
                transfer.status = 'completed'
                transfer.transfer_date = datetime.utcnow()
                transfer.completed_at = datetime.utcnow()
                
                # Update product ownership
                product.current_owner_id = transfer.to_user_id
                product.status = 'active'
                product.sold_at = datetime.utcnow()
                
                # Generate download token for digital products
                if product.product_type == 'digital':
                    from app.utils.security import generate_download_token
                    transfer.download_token = generate_download_token()
                    transfer.download_expires = datetime.utcnow() + timedelta(days=7)
                
                db.session.commit()
                
                # Blockchain: Record ownership transfer on-chain
                try:
                    if current_app.config.get('BLOCKCHAIN_ENABLED', True):
                        bc_config = BlockchainConfig.get_active_config()
                        if bc_config and bc_config.is_contract_deployed and product.blockchain_record:
                            registry = ProductRegistryContract()
                            if registry.is_ready():
                                # Get wallet addresses
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
                                    
                                    # Record blockchain transfer
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
                                    
                                    # Update blockchain product record
                                    product.blockchain_record.current_owner_address = to_wallet.address
                                    db.session.commit()
                                    
                                    current_app.logger.info(f"Blockchain transfer recorded: {tx_result['transaction_hash']}")
                except Exception as bc_error:
                    current_app.logger.error(f"Blockchain transfer error: {bc_error}")
                    # Don't fail the whole transaction if blockchain fails
                
                # Notify buyer that payment was verified
                notify_payment_verified(
                    buyer_id=buyer.id,
                    product_name=product.name
                )
                
                # Log transfer completed
                log_activity(
                    product_id=product.id,
                    activity_type='transfer_completed',
                    user_id=current_user.id,
                    request=request,
                    activity_data={
                        'transfer_id': transfer.id,
                        'from_user_id': transfer.from_user_id,
                        'to_user_id': transfer.to_user_id,
                        'price': str(transfer.sale_price)
                    }
                )
                
                flash('Payment verified! Ownership has been transferred.', 'success')
                return redirect(url_for('orders.my_sales'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Verify receipt error: {e}")
                flash('An error occurred. Please try again.', 'error')
        
        elif action == 'reject':
            try:
                transfer.status = 'rejected'
                transfer.verification_notes = request.form.get('reason', '')
                
                # Re-list the product
                product.is_listed = True
                product.status = 'active'
                
                db.session.commit()
                
                # Notify buyer that payment was rejected
                reason = request.form.get('reason', '')
                notify_payment_rejected(
                    buyer_id=buyer.id,
                    product_name=product.name,
                    reason=reason
                )
                
                # Log transfer rejected
                log_activity(
                    product_id=product.id,
                    activity_type='transfer_rejected',
                    user_id=current_user.id,
                    request=request,
                    activity_data={
                        'transfer_id': transfer.id,
                        'from_user_id': transfer.from_user_id,
                        'to_user_id': transfer.to_user_id,
                        'reason': reason
                    }
                )
                
                flash('Payment rejected. Product has been re-listed.', 'info')
                return redirect(url_for('orders.my_sales'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Reject receipt error: {e}")
                flash('An error occurred. Please try again.', 'error')
    
    return render_template('orders/verify_receipt.html',
                         transfer=transfer,
                         product=product,
                         buyer=buyer)

@bp.route('/update-shipping/<int:transfer_id>', methods=['POST'])
@login_required
def update_shipping(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    if transfer.from_user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    if transfer.status != 'completed':
        flash('Shipping info can only be updated for completed sales.', 'error')
        return redirect(url_for('orders.sale_detail', transfer_id=transfer.id))

    try:
        transfer.tracking_number = request.form.get('tracking_number', '')
        transfer.shipping_carrier = request.form.get('shipping_carrier', '')
        transfer.verification_notes = request.form.get('verification_notes', '')
        db.session.commit()
        flash('Shipping information updated.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update shipping error: {e}")
        flash('An error occurred. Please try again.', 'error')
    return redirect(url_for('orders.sale_detail', transfer_id=transfer.id))

@bp.route('/my-orders')
@login_required
def my_orders():
    orders = OwnershipTransfer.query.filter_by(to_user_id=current_user.id)\
        .order_by(OwnershipTransfer.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)

@bp.route('/order/<int:transfer_id>')
@login_required
def order_detail(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    if transfer.to_user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('orders.my_orders'))
    product = Product.query.get(transfer.product_id)
    seller = User.query.get(transfer.from_user_id)
    return render_template('orders/order_detail.html', transfer=transfer, product=product, seller=seller)

@bp.route('/my-sales')
@login_required
def my_sales():
    sales = OwnershipTransfer.query.filter_by(from_user_id=current_user.id)\
        .order_by(OwnershipTransfer.created_at.desc()).all()
    return render_template('orders/my_sales.html', sales=sales)

@bp.route('/sale/<int:transfer_id>')
@login_required
def sale_detail(transfer_id):
    transfer = OwnershipTransfer.query.get_or_404(transfer_id)
    if transfer.from_user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('orders.my_sales'))
    product = Product.query.get(transfer.product_id)
    buyer = User.query.get(transfer.to_user_id)
    return render_template('orders/sale_detail.html', transfer=transfer, product=product, buyer=buyer)
