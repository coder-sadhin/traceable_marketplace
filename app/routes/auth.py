from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
from app import db
from app.models.user import User
from app.models.notification import Notification
from app.models.product_activity import log_activity
from app.forms.auth_forms import RegistrationForm, LoginForm, ProfileForm, ChangePasswordForm
from app.utils.file_validator import secure_save_file, allowed_image

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        token = user.generate_verification_token()
        try:
            db.session.add(user)
            db.session.commit()
            log_activity(
                activity_type='register',
                user_id=user.id,
                request=request,
                activity_data={'username': user.username, 'email': user.email}
            )
            flash('Registration successful! Please verify your email before logging in.', 'success')
            # Show verification link (in production, send via email)
            verification_url = url_for('auth.verify_email', token=token, _external=True)
            current_app.logger.info(f"Verification URL for {user.email}: {verification_url}")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            if user.is_suspended():
                flash(f'Your account is suspended until {user.suspended_until.strftime("%Y-%m-%d %H:%M")}. Reason: {user.suspension_reason or "Violation of terms"}', 'error')
                return redirect(url_for('auth.login'))
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity(
                activity_type='login',
                user_id=user.id,
                request=request,
                activity_data={'username': user.username}
            )
            next_page = request.form.get('next') or request.args.get('next')
            # Validate next URL to prevent open redirect
            if next_page and not _is_safe_url(next_page):
                next_page = None
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

def _is_safe_url(target):
    """Check if a redirect target is safe (same host)."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    username = current_user.username
    logout_user()
    log_activity(
        activity_type='logout',
        user_id=user_id,
        request=request,
        activity_data={'username': username}
    )
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.bio = form.bio.data
        current_user.bank_details = form.bank_details.data
        
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename and allowed_image(file.filename):
                image_url = secure_save_file(file, 'profiles', prefix='avatar_')
                if image_url:
                    current_user.profile_image = image_url

        # Handle payment QR upload
        if 'payment_qr' in request.files:
            file = request.files['payment_qr']
            if file and file.filename and allowed_image(file.filename):
                qr_url = secure_save_file(file, 'receipts', prefix='qr_')
                if qr_url:
                    current_user.payment_qr_url = qr_url
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.change_password'))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/change_password.html', form=form)

@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    if current_user.is_admin():
        flash('Admin account cannot be deleted.', 'error')
        return redirect(url_for('auth.profile'))
    try:
        current_user.is_active = False
        current_user.username = f'deleted_{current_user.id}'
        current_user.email = f'deleted_{current_user.id}@deleted.com'
        current_user.full_name = None
        current_user.phone = None
        current_user.address = None
        current_user.bio = None
        current_user.bank_details = None
        current_user.profile_image = None
        current_user.payment_qr_url = None
        db.session.commit()
        logout_user()
        flash('Account deleted successfully.', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.profile'))

@bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
    if user.is_verified:
        flash('Your email is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    try:
        user.is_verified = True
        user.verified_at = datetime.utcnow()
        user.verification_token = None
        db.session.commit()
        flash('Email verified successfully! You can now log in.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Verification failed. Please try again.', 'error')
    return redirect(url_for('auth.login'))

@bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email', '')
        user = User.query.filter_by(email=email).first()
        if user and not user.is_verified:
            token = user.generate_verification_token()
            db.session.commit()
            verification_url = url_for('auth.verify_email', token=token, _external=True)
            current_app.logger.info(f"Resend verification URL for {user.email}: {verification_url}")
            flash('Verification link sent! Check your email.', 'success')
        elif user and user.is_verified:
            flash('This email is already verified.', 'info')
        else:
            flash('No account found with that email.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('auth/resend_verification.html')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        # Simulated: in production, send a password reset email
        user = User.query.filter_by(email=email).first()
        if user:
            current_app.logger.info(f"Password reset requested for: {user.email}")
        # Always show success to avoid leaking email existence
        return render_template('auth/forgot_password.html', submitted=True)
    return render_template('auth/forgot_password.html', submitted=False)
