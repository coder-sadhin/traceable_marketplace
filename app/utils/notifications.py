from app import db
from app.models.notification import Notification

def create_notification(user_id, title, message, notification_type='info', related_type=None, related_id=None):
    """Create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_type=related_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def notify_user(user_id, title, message, notification_type='info'):
    """Simple wrapper to notify a user."""
    return create_notification(user_id, title, message, notification_type)

def notify_product_sold(seller_id, product_name, buyer_username, price):
    """Notify seller that their product was purchased."""
    return create_notification(
        user_id=seller_id,
        title=f'Your product has been purchased!',
        message=f'{buyer_username} purchased "{product_name}" for ¥{price:.2f}. Please verify the payment receipt.',
        notification_type='success',
        related_type='product'
    )

def notify_receipt_uploaded(seller_id, product_name, buyer_username):
    """Notify seller that a buyer uploaded a payment receipt."""
    return create_notification(
        user_id=seller_id,
        title=f'New payment receipt uploaded',
        message=f'{buyer_username} uploaded a payment receipt for "{product_name}". Please review and verify it.',
        notification_type='info',
        related_type='order'
    )

def notify_payment_verified(buyer_id, product_name):
    """Notify buyer that payment was verified."""
    return create_notification(
        user_id=buyer_id,
        title=f'Payment verified!',
        message=f'Your payment for "{product_name}" has been verified. Ownership has been transferred to you.',
        notification_type='success',
        related_type='order'
    )

def notify_payment_rejected(buyer_id, product_name, reason=''):
    """Notify buyer that payment was rejected."""
    msg = f'Your payment for "{product_name}" was rejected.'
    if reason:
        msg += f' Reason: {reason}'
    return create_notification(
        user_id=buyer_id,
        title=f'Payment rejected',
        message=msg,
        notification_type='error',
        related_type='order'
    )

def notify_new_listing(creator_id, product_name, product_code):
    """Notify creator that product was submitted for review."""
    return create_notification(
        user_id=creator_id,
        title=f'Product submitted for review',
        message=f'"{product_name}" ({product_code}) has been submitted and is awaiting admin approval.',
        notification_type='info',
        related_type='product'
    )

def get_unread_count(user_id):
    """Get count of unread notifications for a user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()

def notify_royalty_paid(creator_id, amount, transfer_id):
    """Notify creator that royalty payment was processed."""
    return create_notification(
        user_id=creator_id,
        title='Royalty Payment Received',
        message=f'You have received a royalty payment of ¥{amount:.2f} from a secondary sale.',
        notification_type='success',
        related_type='transfer',
        related_id=transfer_id
    )

def notify_product_approved(creator_id, product_name, product_code):
    """Notify creator that product was approved."""
    return create_notification(
        user_id=creator_id,
        title='Product Approved!',
        message=f'Your product "{product_name}" ({product_code}) has been approved and is now listed for sale.',
        notification_type='success',
        related_type='product'
    )

def notify_product_rejected(creator_id, product_name, reason=''):
    """Notify creator that product was rejected."""
    msg = f'Your product "{product_name}" has been rejected.'
    if reason:
        msg += f' Reason: {reason}'
    return create_notification(
        user_id=creator_id,
        title='Product Rejected',
        message=msg,
        notification_type='error',
        related_type='product'
    )

def notify_message_received(user_id, sender_username):
    """Notify user of a new message."""
    return create_notification(
        user_id=user_id,
        title='New Message',
        message=f'You have received a new message from {sender_username}.',
        notification_type='info',
        related_type='message'
    )

def notify_wishlist_item_sold(user_id, product_name):
    """Notify user that a wishlist item was sold."""
    return create_notification(
        user_id=user_id,
        title='Wishlist Item Sold',
        message=f'"{product_name}" from your wishlist has been sold.',
        notification_type='info',
        related_type='product'
    )

def notify_account_suspended(user_id, reason, end_date):
    """Notify user that their account was suspended."""
    return create_notification(
        user_id=user_id,
        title='Account Suspended',
        message=f'Your account has been suspended until {end_date}. Reason: {reason}',
        notification_type='error'
    )
