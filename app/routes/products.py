from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.review import Review
from app.models.wishlist import Wishlist
from app.models.product_activity import ProductActivity, log_activity
from app.forms.product_forms import ProductForm, ResaleForm
from app.utils.file_validator import secure_save_file, allowed_image
from app.utils.qr_generator import generate_product_qr
from app.utils.notifications import notify_new_listing
from datetime import datetime

bp = Blueprint('products', __name__)

def generate_unique_code():
    import random
    prefix = 'HMP'
    year = datetime.utcnow().year
    number = random.randint(1000, 9999)
    code = f"{prefix}-{year}-{number}"
    # Check uniqueness
    while Product.query.filter_by(unique_code=code).first():
        number = random.randint(1000, 9999)
        code = f"{prefix}-{year}-{number}"
    return code

@bp.route('/browse')
def browse():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    condition = request.args.get('condition', '')
    product_type = request.args.get('product_type', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    
    query = Product.query.filter_by(is_listed=True, is_approved=True)
    
    if category:
        query = query.filter_by(category=category)
    if condition:
        query = query.filter_by(condition=condition)
    if product_type:
        query = query.filter_by(product_type=product_type)
    if location:
        safe_location = location.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(Product.location.ilike(f'%{safe_location}%'))
    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)
    if search:
        safe_search = search.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(Product.name.ilike(f'%{safe_search}%'))
        # Log search activity
        try:
            activity = ProductActivity(
                activity_type='search',
                user_id=current_user.id if current_user.is_authenticated else None,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:255] if request.user_agent.string else None,
                activity_data={'search_query': search}
            )
            db.session.add(activity)
            db.session.commit()
        except Exception:
            db.session.rollback()
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Product.listed_at >= date_from)
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(Product.listed_at <= date_to)
        except ValueError:
            pass
    
    if sort == 'price_asc':
        query = query.order_by(Product.current_price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.current_price.desc())
    elif sort == 'oldest':
        query = query.order_by(Product.listed_at.asc())
    elif sort == 'popular':
        # Sort by activity count - need to use raw sql with join
        from sqlalchemy import func
        query = db.session.query(
            Product,
            func.count(ProductActivity.id).label('activity_count')
        ).outerjoin(
            ProductActivity, Product.id == ProductActivity.product_id
        ).filter(
            Product.is_listed == True,
            Product.is_approved == True
        ).group_by(Product.id).order_by(func.count(ProductActivity.id).desc())
        products = query.paginate(
            page=page, per_page=current_app.config['PRODUCTS_PER_PAGE'], error_out=False
        )
        # Extract products from tuples
        featured = [p[0] for p in products.items]
        products.items = featured
        return render_template('products/browse.html', products=products)
    else:
        query = query.order_by(Product.listed_at.desc())
    
    products = query.paginate(
        page=page, per_page=current_app.config['PRODUCTS_PER_PAGE'], error_out=False
    )
    
    return render_template('products/browse.html', products=products)

@bp.route('/list', methods=['GET', 'POST'])
@login_required
def list_product():
    if current_user.is_suspended():
        flash('Your account is suspended. You cannot list products.', 'error')
        return redirect(url_for('main.index'))
    
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            unique_code=generate_unique_code(),
            name=form.name.data,
            description=form.description.data,
            product_type=form.product_type.data,
            category=form.category.data,
            creator_id=current_user.id,
            current_owner_id=current_user.id,
            current_price=form.current_price.data,
            original_price=form.current_price.data,
            condition=form.condition.data,
            condition_description=form.condition_description.data,
            location=form.location.data,
            dimensions=form.dimensions.data,
            weight=form.weight.data,
            is_listed=False,
            is_approved=False,
            status='pending_approval'
        )
        
        # Handle image uploads
        image_urls = []
        for field_name in ['image1', 'image2', 'image3']:
            if field_name in request.files:
                file = request.files[field_name]
                if file and file.filename and allowed_image(file.filename):
                    img_url = secure_save_file(file, 'products')
                    if img_url:
                        image_urls.append(img_url)
        
        product.image_urls = image_urls
        
        db.session.add(product)
        db.session.commit()
        
        # Generate QR code
        try:
            qr_url = generate_product_qr(product)
            product.qr_code_url = qr_url
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"QR generation failed: {e}")
        
        # Notify user
        notify_new_listing(
            creator_id=current_user.id,
            product_name=product.name,
            product_code=product.unique_code
        )
        
        flash(f'Product submitted for review! Code: {product.unique_code}. Admin will approve it shortly.', 'success')
        return redirect(url_for('products.product_detail', product_code=product.unique_code))
    
    return render_template('products/list.html', form=form)

@bp.route('/<product_code>')
def product_detail(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    ownership_history = product.get_ownership_history()
    
    # Log view activity
    try:
        activity = ProductActivity(
            product_id=product.id,
            activity_type='view',
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:255] if request.user_agent.string else None
        )
        db.session.add(activity)
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    return render_template('products/detail.html', product=product, history=ownership_history)

@bp.route('/<product_code>/resell', methods=['GET', 'POST'])
@login_required
def resell_product(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    if product.current_owner_id != current_user.id:
        flash('You can only resell items you own.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))

    form = ResaleForm()
    if form.validate_on_submit():
        product.current_price = form.current_price.data
        product.condition = form.condition.data
        product.condition_description = form.condition_description.data
        product.is_approved = True
        product.is_listed = True
        product.status = 'active'
        product.listed_at = datetime.utcnow()
        
        # Handle new images
        image_urls = []
        for field_name in ['image1', 'image2', 'image3']:
            if field_name in request.files:
                file = request.files[field_name]
                if file and file.filename and allowed_image(file.filename):
                    img_url = secure_save_file(file, 'products')
                    if img_url:
                        image_urls.append(img_url)
        
        if image_urls:
            product.image_urls = image_urls
        
        db.session.commit()
        flash('Product listed for resale!', 'success')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    return render_template('products/resell.html', product=product, form=form)

@bp.route('/<product_code>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    # Only creator or current owner can edit
    if product.current_owner_id != current_user.id and product.creator_id != current_user.id:
        flash('You do not have permission to edit this product.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    # Cannot edit if pending sale
    if product.status == 'pending_sale':
        flash('Cannot edit product while a sale is pending.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    form = ProductForm(obj=product)
    
    if request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.product_type.data = product.product_type
        form.category.data = product.category
        form.current_price.data = product.current_price
        form.condition.data = product.condition
        form.condition_description.data = product.condition_description
        form.location.data = product.location
        form.dimensions.data = product.dimensions
        form.weight.data = product.weight
    
    if form.validate_on_submit():
        try:
            product.name = form.name.data
            product.description = form.description.data
            product.product_type = form.product_type.data
            product.category = form.category.data
            product.current_price = form.current_price.data
            product.condition = form.condition.data
            product.condition_description = form.condition_description.data
            product.location = form.location.data
            product.dimensions = form.dimensions.data
            product.weight = form.weight.data
            product.updated_at = datetime.utcnow()
            
            # Handle new image uploads (append to existing)
            new_image_urls = []
            for field_name in ['image1', 'image2', 'image3']:
                if field_name in request.files:
                    file = request.files[field_name]
                    if file and file.filename and allowed_image(file.filename):
                        img_url = secure_save_file(file, 'products')
                        if img_url:
                            new_image_urls.append(img_url)
            
            if new_image_urls:
                existing = product.image_urls or []
                product.image_urls = existing + new_image_urls
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products.product_detail', product_code=product_code))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Edit product error: {e}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('products/edit.html', product=product, form=form)

@bp.route('/<product_code>/unlist', methods=['POST'])
@login_required
def unlist_product(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    if product.current_owner_id != current_user.id:
        flash('You can only unlist items you own.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    if product.status == 'pending_sale':
        flash('Cannot unlist product while a sale is pending.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    try:
        product.is_listed = False
        product.status = 'inactive'
        db.session.commit()
        flash('Product has been unlisted.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unlist product error: {e}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('products.my_products'))

@bp.route('/<product_code>/delete', methods=['POST'])
@login_required
def delete_product(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    
    # Only creator can delete, and only if no completed transfers
    if product.creator_id != current_user.id:
        flash('Only the creator can delete a product.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    # Check if there are completed transfers (ownership changes)
    completed_transfers = OwnershipTransfer.query.filter_by(
        product_id=product.id, status='completed'
    ).count()
    
    if completed_transfers > 0:
        flash('Cannot delete product that has been sold. You can unlist it instead.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.', 'success')
        return redirect(url_for('products.my_products'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete product error: {e}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))

@bp.route('/my-products')
@login_required
def my_products():
    owned = Product.query.filter_by(current_owner_id=current_user.id).order_by(Product.created_at.desc()).all()
    created = Product.query.filter_by(creator_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template('products/my_products.html', owned=owned, created=created)

@bp.route('/<product_code>/reviews')
def product_reviews(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
    average_rating = db.session.query(db.func.avg(Review.rating)).filter_by(product_id=product.id).scalar() or 0
    review_count = len(reviews)
    rating_breakdown = {}
    for r in reviews:
        rating_breakdown[r.rating] = rating_breakdown.get(r.rating, 0) + 1
    for stars in range(1, 6):
        if review_count > 0:
            rating_breakdown[stars] = round((rating_breakdown.get(stars, 0) / review_count) * 100)
        else:
            rating_breakdown[stars] = 0
    can_review = False
    has_purchased = False
    if current_user.is_authenticated:
        has_purchased = OwnershipTransfer.query.filter_by(
            product_id=product.id, to_user_id=current_user.id, status='completed'
        ).first() is not None
        can_review = has_purchased and Review.query.filter_by(product_id=product.id, user_id=current_user.id).first() is None
    return render_template('products/reviews.html', product=product, reviews=reviews,
                           average_rating=average_rating, review_count=review_count,
                           rating_breakdown=rating_breakdown, can_review=can_review,
                           has_purchased=has_purchased)

@bp.route('/<product_code>/review', methods=['POST'])
@login_required
def submit_review(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    from app.models.review import Review
    from app.forms.review_forms import ReviewForm
    
    # Check if user has purchased this product
    purchased = OwnershipTransfer.query.filter_by(
        product_id=product.id, to_user_id=current_user.id, status='completed'
    ).first()
    if not purchased:
        flash('You can only review products you have purchased.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    # Check if already reviewed
    existing = Review.query.filter_by(product_id=product.id, user_id=current_user.id).first()
    if existing:
        flash('You have already reviewed this product.', 'error')
        return redirect(url_for('products.product_detail', product_code=product_code))
    
    form = ReviewForm()
    if form.validate_on_submit():
        try:
            review = Review(
                product_id=product.id,
                user_id=current_user.id,
                rating=form.rating.data,
                title=form.title.data,
                body=form.body.data
            )
            db.session.add(review)
            db.session.commit()
            log_activity(
                product_id=product.id,
                activity_type='review_submitted',
                user_id=current_user.id,
                request=request,
                activity_data={'product_code': product_code, 'rating': form.rating.data}
            )
            flash('Review submitted!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit review.', 'error')
    
    return redirect(url_for('products.product_detail', product_code=product_code))

# ==================== WISHLIST / FAVORITES ====================
@bp.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template('products/wishlist.html', items=items)

@bp.route('/<product_code>/favorite', methods=['POST'])
@login_required
def toggle_favorite(product_code):
    product = Product.query.filter_by(unique_code=product_code).first_or_404()
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    try:
        if existing:
            db.session.delete(existing)
            db.session.commit()
            log_activity(
                product_id=product.id,
                activity_type='wishlist_remove',
                user_id=current_user.id,
                request=request,
                activity_data={'product_code': product_code}
            )
            flash('Removed from wishlist.', 'info')
        else:
            item = Wishlist(user_id=current_user.id, product_id=product.id)
            db.session.add(item)
            db.session.commit()
            log_activity(
                product_id=product.id,
                activity_type='wishlist_add',
                user_id=current_user.id,
                request=request,
                activity_data={'product_code': product_code}
            )
            flash('Added to wishlist!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    return redirect(url_for('products.product_detail', product_code=product_code))
