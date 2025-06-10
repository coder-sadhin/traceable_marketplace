from datetime import datetime
from app import db

class BlockchainTransfer(db.Model):
    __tablename__ = 'blockchain_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    blockchain_product_id = db.Column(db.Integer, db.ForeignKey('blockchain_products.id'), nullable=False, index=True)
    ownership_transfer_id = db.Column(db.Integer, db.ForeignKey('ownership_transfers.id'), nullable=True, index=True)
    
    # On-chain addresses
    from_address = db.Column(db.String(42), nullable=False)
    to_address = db.Column(db.String(42), nullable=False)
    
    # Transaction details
    transaction_hash = db.Column(db.String(66), nullable=False, unique=True, index=True)
    block_number = db.Column(db.Integer)
    gas_used = db.Column(db.Integer)
    
    # Status
    status = db.Column(db.String(20), default='pending')
    confirmed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BlockchainTransfer tx={self.transaction_hash[:20]}...>'
