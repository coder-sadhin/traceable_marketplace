import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Login config
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create upload directories
    upload_dirs = ['products', 'receipts', 'qrcodes', 'profiles']
    for dir_name in upload_dirs:
        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
        os.makedirs(dir_path, exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.products import bp as products_bp
    from app.routes.orders import bp as orders_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.main import bp as main_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.messages import bp as messages_bp
    from app.routes.users import bp as users_bp
    from app.routes.royalties import bp as royalties_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(royalties_bp, url_prefix='/royalties')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Context processor for notifications
    @app.context_processor
    def inject_notifications():
        from app.utils.notifications import get_unread_count
        from flask_login import current_user
        if current_user.is_authenticated:
            return dict(unread_notifications=get_unread_count(current_user.id))
        return dict(unread_notifications=0)
    
    # Context processor for admin pending count
    @app.context_processor
    def inject_admin_pending():
        from flask_login import current_user
        if current_user.is_authenticated and current_user.is_admin():
            from app.models.product import Product
            from app.models.ownership_transfer import OwnershipTransfer
            pending = Product.query.filter_by(status='pending_approval').count()
            pending_payouts = OwnershipTransfer.query.filter_by(status='completed', seller_paid=False).count()
            return dict(pending_count=pending, pending_seller_payouts=pending_payouts)
        return dict(pending_count=0, pending_seller_payouts=0)

    # Context processor for active announcements (only for authenticated users)
    @app.context_processor
    def inject_announcements():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models.announcement import Announcement
            active = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
            return dict(active_announcements=active, active_announcement_count=len(active))
        return dict(active_announcements=[], active_announcement_count=0)

    return app
