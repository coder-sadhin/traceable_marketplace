from datetime import datetime
from app import db

class OwnershipTransfer(db.Model):
    __tablename__ = 'ownership_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Sale details
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    royalty_amount = db.Column(db.Numeric(10, 2), default=0)
    royalty_percentage = db.Column(db.Numeric(5, 2))
    platform_fee = db.Column(db.Numeric(10, 2), default=0)
    platform_fee_percentage = db.Column(db.Numeric(5, 2), default=3)
    
    # Payment
    payment_receipt_url = db.Column(db.String(255))
    payment_method = db.Column(db.String(50), default='bank_transfer')
    
    # Seller Payout (admin pays seller after verification)
    seller_paid = db.Column(db.Boolean, default=False)
    seller_paid_at = db.Column(db.DateTime)
    seller_paid_notes = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='pending', index=True)
    
    # Shipping
    tracking_number = db.Column(db.String(100))
    shipping_carrier = db.Column(db.String(50))
    shipping_status = db.Column(db.String(20))
    
    # Digital delivery
    download_token = db.Column(db.String(255))
    download_expires = db.Column(db.DateTime)
    
    # Verification
    verification_notes = db.Column(db.Text)
    
    # Timestamps
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship: One ownership transfer can have one blockchain record
    blockchain_transfer = db.relationship('BlockchainTransfer', backref='ownership_transfer', uselist=False)
    
    def calculate_royalty(self):
        if self.royalty_percentage and self.sale_price:
            return float(self.sale_price) * float(self.royalty_percentage) / 100
        return 0

    def calculate_platform_fee(self):
        if self.sale_price:
            return float(self.sale_price) * float(self.platform_fee_percentage or 3) / 100
        return 0

    def seller_receives(self):
        """Amount the seller actually receives after royalty and platform fee."""
        result = float(self.sale_price) - float(self.royalty_amount or 0) - float(self.platform_fee or 0)
        return max(result, 0)
    
    def is_pending_seller_payout(self):
        """Check if this transfer is completed but seller hasn't been paid yet."""
        return self.status == 'completed' and not self.seller_paid
    
    def has_blockchain_record(self):
        """Check if this transfer has an on-chain blockchain record."""
        return self.blockchain_transfer is not None and self.blockchain_transfer.status == 'confirmed'
    
    def __repr__(self):
        return f'<Transfer {self.id}: Product {self.product_id}>'
