# Traceable Marketplace

A blockchain-integrated digital marketplace for buying and selling digital products with complete ownership traceability, royalty tracking, and comprehensive activity logging.

## Features

### Core Marketplace
- **Product Listings**: Browse, search, and filter digital products
- **Secure Transactions**: Admin-verified payment receipts and ownership transfers
- **User Reviews**: Rate and review purchased products
- **Wishlist System**: Save products for later purchase
- **Category Management**: Organize products into categories

### Blockchain Integration
- **Product Minting**: Each product is minted as an NFT on the blockchain
- **Ownership Tracking**: Complete traceability of product ownership history
- **Smart Contracts**: Automated royalty distribution and ownership transfers
- **QR Code Generation**: Blockchain-verified product authenticity

### Admin Dashboard
- **Product Management**: Approve, reject, list, and delete products
- **User Management**: Verify, suspend, and manage user accounts
- **Activity Logs**: Comprehensive logging of all system activities
- **Payment Verification**: Verify and process payment receipts
- **Royalty Tracking**: Track and manage royalty payments to creators

### Activity Logging System
- **Product Activities**: Views, searches, wishlist actions, reviews
- **Order Activities**: Checkout views, transfers, receipts, completions
- **Auth Activities**: Registrations, logins, logouts
- **Admin Activities**: User actions, product actions, approvals, suspensions

### User Features
- **Profile Management**: Update profile information and avatar
- **Notifications**: Real-time notifications for important events
- **Messaging**: Direct messaging between users
- **Purchase History**: Track all purchases and sales
- **Royalty Earnings**: View and manage royalty income

## Tech Stack

### Backend
- **Flask 3.0+**: Python web framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Login**: User authentication and session management
- **Flask-Migrate**: Database migrations
- **Flask-WTF**: Form handling with CSRF protection

### Frontend
- **Jinja2**: Template engine
- **Tailwind CSS**: Utility-first CSS framework
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization (optional)

### Database
- **SQLite** (development)
- **PostgreSQL** (production)

### Blockchain
- **Web3.py**: Ethereum blockchain interaction
- **Solidity**: Smart contract development
- **Ganache** (development) / **Ethereum** (production)

### Other
- **QRCode**: QR code generation
- **Pillow**: Image processing
- **Bcrypt**: Password hashing
- **Email-Validator**: Email validation

## Project Structure

```
traceable-marketplace/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/                  # Database models
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── product_activity.py  # Activity logging
│   │   ├── ownership_transfer.py
│   │   ├── review.py
│   │   ├── message.py
│   │   ├── notification.py
│   │   ├── category.py
│   │   ├── royalty_payment.py
│   │   ├── announcement.py
│   │   ├── wishlist.py
│   │   └── blockchain_*.py      # Blockchain models
│   ├── routes/                  # Application routes
│   │   ├── auth.py              # Authentication
│   │   ├── products.py          # Product management
│   │   ├── orders.py            # Order processing
│   │   ├── admin.py             # Admin dashboard
│   │   ├── main.py              # Main pages
│   │   ├── notifications.py
│   │   ├── messages.py
│   │   ├── users.py
│   │   └── royalties.py
│   ├── forms/                   # WTForms
│   ├── templates/               # Jinja2 templates
│   │   ├── admin/
│   │   ├── auth/
│   │   ├── main/
│   │   ├── orders/
│   │   ├── products/
│   │   └── users/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/             # User uploads
│   ├── utils/                   # Utility functions
│   │   ├── file_validator.py
│   │   ├── qr_generator.py
│   │   └── notifications.py
│   └── blockchain/              # Blockchain integration
│       ├── contract.py
│       └── utils.py
├── migrations/                  # Database migrations
├── config.py                    # Application configuration
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── create_admin.py              # Create admin user
└── seed_data.py                 # Seed database with test data
```

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL (optional, for production)
- Node.js & npm (for blockchain development)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd traceable-marketplace
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   ```

6. **Create admin user**
   ```bash
   python create_admin.py
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5001`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-key-change-in-production-abc123` |
| `DATABASE_URL` | Database connection string | `sqlite:///app.db` |
| `BASE_URL` | Application base URL | `http://localhost:5001` |
| `BLOCKCHAIN_ENABLED` | Enable blockchain features | `true` |
| `BLOCKCHAIN_RPC_URL` | Blockchain RPC endpoint | `http://127.0.0.1:8545` |
| `BLOCKCHAIN_CHAIN_ID` | Blockchain network ID | `1337` |
| `BLOCKCHAIN_NETWORK` | Network name | `ganache` |

### Application Settings

Edit `config.py` to customize:
- Products per page
- Default royalty percentage
- File upload settings
- Maximum content length

## Usage

### For Users

1. **Register**: Create an account with email verification
2. **Browse Products**: Explore the marketplace with search and filters
3. **Purchase**: Buy products with admin-verified payment
4. **Track Orders**: View order status and ownership history
5. **Leave Reviews**: Rate and review purchased products
6. **Earn Royalties**: Receive royalties when your products are resold

### For Admins

1. **Dashboard**: View pending approvals and system statistics
2. **Product Management**: Approve, reject, and manage products
3. **User Management**: Verify users, suspend accounts, manage access
4. **Activity Logs**: Monitor all system activities with detailed filters
5. **Payment Verification**: Verify payment receipts and process transfers
6. **Royalty Tracking**: Track and manage royalty payments

### Activity Logs

The system logs all activities including:
- Product views and searches
- Wishlist additions and removals
- Review submissions
- Order initiation and completion
- Payment uploads and verifications
- User registrations and logins
- Admin actions (approvals, suspensions, deletions)

View logs in the admin dashboard under Products → View Logs

## Blockchain Setup

### Development (Ganache)

1. **Install Ganache**
   ```bash
   npm install -g ganache
   ```

2. **Start Ganache**
   ```bash
   ganache
   ```

3. **Deploy Smart Contract**
   ```bash
   # Contract deployment is handled automatically on product approval
   ```

### Production (Ethereum)

1. **Configure RPC URL**
   ```env
   BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
   BLOCKCHAIN_CHAIN_ID=1
   BLOCKCHAIN_NETWORK=ethereum
   ```

2. **Deploy Smart Contract**
   ```bash
   # Use Remix or Hardhat to deploy the contract
   ```

## API Documentation

### Activity Logging Helper

```python
from app.models.product_activity import log_activity

# Log a product view
log_activity(
    product_id=product.id,
    activity_type='view',
    user_id=current_user.id,
    request=request
)

# Log a custom activity
log_activity(
    product_id=product.id,
    activity_type='custom_event',
    user_id=current_user.id,
    request=request,
    activity_data={'key': 'value'}
)
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper email service
- [ ] Set up proper file storage (S3, etc.)
- [ ] Enable HTTPS
- [ ] Configure production blockchain RPC
- [ ] Set up proper logging
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerts

### Deployment with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 run:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.

## Changelog

### Version 1.0.0 (June 2025)
- Initial release
- Core marketplace functionality
- Blockchain integration
- Activity logging system
- Admin dashboard
- User management
- Royalty tracking