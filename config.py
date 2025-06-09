import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-abc123'
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5001')
    
    # Database - use SQLite for development if PostgreSQL is not available
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    
    # Application
    PRODUCTS_PER_PAGE = 12
    ROYALTY_PERCENTAGE_DEFAULT = 5.0
    
    # Blockchain Configuration
    BLOCKCHAIN_ENABLED = os.environ.get('BLOCKCHAIN_ENABLED', 'true').lower() == 'true'
    BLOCKCHAIN_RPC_URL = os.environ.get('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:8545')
    BLOCKCHAIN_CHAIN_ID = int(os.environ.get('BLOCKCHAIN_CHAIN_ID', 1337))
    BLOCKCHAIN_NETWORK = os.environ.get('BLOCKCHAIN_NETWORK', 'ganache')
