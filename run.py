from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.review import Review
from app.models.message import Message
from app.models.notification import Notification
from app.models.category import Category
from app.models.royalty_payment import RoyaltyPayment
from app.models.announcement import Announcement
from app.models.wishlist import Wishlist

app = create_app()

# Auto-create all database tables on startup
with app.app_context():
    db.create_all()
    print("✅ Database tables verified.")

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'OwnershipTransfer': OwnershipTransfer,
        'Review': Review,
        'Message': Message,
        'Notification': Notification,
        'Category': Category,
        'RoyaltyPayment': RoyaltyPayment,
        'Announcement': Announcement,
        'Wishlist': Wishlist,
    }

if __name__ == '__main__':
    app.run(debug=True)
