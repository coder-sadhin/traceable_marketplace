#!/usr/bin/env python3
"""
CLI command to create the admin user.
Only ONE admin is allowed in the system.
This script also initializes the database if needed.

Usage: python create_admin.py <username> <email> <password>
Example: python create_admin.py admin admin@example.com SecurePass123
"""
import sys
import os

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.ownership_transfer import OwnershipTransfer
from app.models.review import Review
from app.models.message import Message
from app.models.notification import Notification
from app.models.category import Category
from app.models.royalty_payment import RoyaltyPayment
from app.models.announcement import Announcement
from app.models.wishlist import Wishlist

ALL_MODELS = [User, Product, OwnershipTransfer, Review, Message, Notification, Category, RoyaltyPayment, Announcement, Wishlist]

def create_tables_if_needed():
    """Create all database tables if they don't exist."""
    db.create_all()
    print("✅ Database tables created/verified.")

def create_admin(username, email, password):
    app = create_app()
    with app.app_context():
        # Step 1: Ensure all tables exist
        create_tables_if_needed()

        # Step 2: Check if admin already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"⚠️  Admin already exists! (Username: {existing_admin.username})")
            print("Only one admin is allowed in the system.")
            return False

        # Step 3: Check if username or email already taken
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' already taken.")
            return False
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already registered.")
            return False

        # Step 4: Create admin user
        admin = User(
            username=username,
            email=email,
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        print(f"\n✅ Admin created successfully!")
        print(f"   Username: {username}")
        print(f"   Email:    {email}")
        print(f"   Role:     admin")
        print(f"\n   Start the app:  python run.py")
        print(f"   Login at:       http://localhost:5000/auth/login")
        return True

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        print("Example: python create_admin.py admin admin@example.com SecurePass123")
        sys.exit(1)

    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]

    create_admin(username, email, password)
