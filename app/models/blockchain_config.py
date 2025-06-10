from datetime import datetime
from app import db

class BlockchainConfig(db.Model):
    __tablename__ = 'blockchain_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Network settings
    network = db.Column(db.String(20), default='ganache')
    rpc_url = db.Column(db.String(255), default='http://127.0.0.1:8545')
    chain_id = db.Column(db.Integer, default=1337)
    
    # Contract
    contract_address = db.Column(db.String(42))
    contract_abi = db.Column(db.JSON)
    deployed_at = db.Column(db.DateTime)
    deployer_address = db.Column(db.String(42))
    
    # Platform wallet
    platform_address = db.Column(db.String(42))
    platform_private_key = db.Column(db.String(66))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_contract_deployed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_active_config(cls):
        return cls.query.filter_by(is_active=True).first()
    
    def __repr__(self):
        return f'<BlockchainConfig network={self.network} contract={self.contract_address}>'
