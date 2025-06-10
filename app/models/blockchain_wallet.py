from datetime import datetime
from app import db

class BlockchainWallet(db.Model):
    __tablename__ = 'blockchain_wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Wallet details
    address = db.Column(db.String(42), nullable=False, unique=True, index=True)
    private_key_encrypted = db.Column(db.Text, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('blockchain_wallet', uselist=False))
    
    def __repr__(self):
        return f'<BlockchainWallet user={self.user_id} address={self.address[:10]}...>'
