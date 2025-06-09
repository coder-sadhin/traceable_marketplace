from datetime import datetime
from app import db

class RoyaltyPayment(db.Model):
    __tablename__ = 'royalty_payments'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('ownership_transfers.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    paid_at = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    reference = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='royalty_payments')
    transfer = db.relationship('OwnershipTransfer', backref='royalty_payment')

    def __repr__(self):
        return f'<RoyaltyPayment {self.id} ¥{self.amount}>'
