from datetime import datetime
from app import db

class BlockchainProduct(db.Model):
    __tablename__ = 'blockchain_products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True, index=True)
    token_id = db.Column(db.Integer, nullable=False, unique=True, index=True)
    contract_address = db.Column(db.String(42), nullable=False)
    network = db.Column(db.String(20), default='ganache')
    metadata_uri = db.Column(db.String(500))
    transaction_hash = db.Column(db.String(66))
    block_number = db.Column(db.Integer)
    
    # Status
    is_minted = db.Column(db.Boolean, default=False)
    minted_at = db.Column(db.DateTime)
    
    # Current on-chain owner
    current_owner_address = db.Column(db.String(42))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref=db.backref('blockchain_record', uselist=False))
    transfers = db.relationship('BlockchainTransfer', backref='blockchain_product', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BlockchainProduct token={self.token_id} product={self.product_id}>'
