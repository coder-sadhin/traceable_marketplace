import secrets
from datetime import datetime, timedelta

def generate_secure_token(length=32):
    return secrets.token_urlsafe(length)

def generate_download_token():
    return secrets.token_urlsafe(32)
