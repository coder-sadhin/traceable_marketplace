import os
import secrets
from cryptography.fernet import Fernet
from eth_account import Account

# Use a fixed key derived from SECRET_KEY for encryption
# In production, use a proper key management system

def get_fernet():
    from flask import current_app
    key = current_app.config.get('SECRET_KEY', 'dev-key-change-in-production-abc123')
    # Derive a 32-byte base64-encoded key for Fernet
    import base64
    import hashlib
    hashed = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)
    return Fernet(fernet_key)

def generate_wallet():
    """Generate a new Ethereum wallet."""
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)
    return {
        'address': account.address,
        'private_key': private_key
    }

def encrypt_private_key(private_key):
    """Encrypt a private key using Fernet."""
    f = get_fernet()
    return f.encrypt(private_key.encode()).decode()

def decrypt_private_key(encrypted_key):
    """Decrypt a private key using Fernet."""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()

def get_contract_abi():
    """Return the compiled ABI of the ProductRegistry contract.
    
    This ABI must match the simplified ProductRegistry.sol exactly.
    The contract has: mintProduct, transferOwnership, getProduct,
    getProductByCode, verifyProduct, totalSupply, plus state variables.
    """
    return [
        {
            "inputs": [],
            "stateMutability": "nonpayable",
            "type": "constructor"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
                {"indexed": False, "internalType": "string", "name": "productCode", "type": "string"},
                {"indexed": True, "internalType": "address", "name": "creator", "type": "address"}
            ],
            "name": "ProductMinted",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
                {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
                {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"}
            ],
            "name": "OwnershipTransferred",
            "type": "event"
        },
        {
            "inputs": [
                {"internalType": "string", "name": "productCode", "type": "string"},
                {"internalType": "string", "name": "metadataURI", "type": "string"},
                {"internalType": "address", "name": "creator", "type": "address"}
            ],
            "name": "mintProduct",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "price", "type": "uint256"}
            ],
            "name": "transferOwnership",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
            "name": "getProduct",
            "outputs": [
                {"internalType": "uint256", "name": "id", "type": "uint256"},
                {"internalType": "string", "name": "code", "type": "string"},
                {"internalType": "string", "name": "uri", "type": "string"},
                {"internalType": "address", "name": "creator", "type": "address"},
                {"internalType": "address", "name": "currentOwner", "type": "address"},
                {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                {"internalType": "bool", "name": "exists", "type": "bool"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "string", "name": "productCode", "type": "string"}],
            "name": "getProductByCode",
            "outputs": [
                {"internalType": "uint256", "name": "id", "type": "uint256"},
                {"internalType": "string", "name": "uri", "type": "string"},
                {"internalType": "address", "name": "creator", "type": "address"},
                {"internalType": "address", "name": "currentOwner", "type": "address"},
                {"internalType": "uint256", "name": "createdAt", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
            "name": "verifyProduct",
            "outputs": [
                {"internalType": "bool", "name": "valid", "type": "bool"},
                {"internalType": "address", "name": "creator", "type": "address"},
                {"internalType": "address", "name": "currentOwner", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "name": "products",
            "outputs": [
                {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
                {"internalType": "string", "name": "productCode", "type": "string"},
                {"internalType": "string", "name": "metadataURI", "type": "string"},
                {"internalType": "address", "name": "creator", "type": "address"},
                {"internalType": "address", "name": "currentOwner", "type": "address"},
                {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                {"internalType": "bool", "name": "exists", "type": "bool"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "string", "name": "", "type": "string"}],
            "name": "productCodeToTokenId",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
