import os
import sys
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.ownership_transfer import OwnershipTransfer
from app.models.review import Review
from app.models.message import Message
from app.models.notification import Notification
from app.models.wishlist import Wishlist
from app.models.royalty_payment import RoyaltyPayment
from app.models.announcement import Announcement
from app.models.blockchain_wallet import BlockchainWallet
from app.blockchain.utils import generate_wallet, encrypt_private_key

app = create_app()

# ============== CONFIGURATION ==============
PRODUCT_IMAGES = [
    "/static/uploads/products/product_01.jpg",
    "/static/uploads/products/product_02.jpg",
    "/static/uploads/products/product_03.jpg",
    "/static/uploads/products/product_04.jpg",
    "/static/uploads/products/product_05.jpg",
    "/static/uploads/products/product_06.jpg",
    "/static/uploads/products/product_07.jpg",
    "/static/uploads/products/product_08.jpg",
    "/static/uploads/products/product_09.jpg",
    "/static/uploads/products/product_10.jpg",
    "/static/uploads/products/product_11.jpg",
    "/static/uploads/products/product_12.jpg",
    "/static/uploads/products/product_13.jpg",
    "/static/uploads/products/product_14.jpg",
    "/static/uploads/products/product_15.jpg",
]

PROFILE_IMAGES = [
    "/static/uploads/profiles/profile_01.jpg",
    "/static/uploads/profiles/profile_02.jpg",
    "/static/uploads/profiles/profile_03.jpg",
    "/static/uploads/profiles/profile_04.jpg",
    "/static/uploads/profiles/profile_05.jpg",
]

CONDITIONS = ["new", "used"]
LOCATIONS = [
    "Jingdezhen, China", "Kyoto, Japan", "Seville, Spain", "Istanbul, Turkey",
    "Fez, Morocco", "Cappadocia, Turkey", "Sedona, USA", "Ubud, Indonesia",
    "Lisbon, Portugal", "Marrakech, Morocco", "Taos, USA", "Arita, Japan",
    "Deruta, Italy", "Talavera, Mexico", "Mashiko, Japan"
]


def get_three_images(index):
    """Get 3 images for a product - same base image but different angles.
    Uses 3 consecutive images from the pool to simulate different angles of the same product."""
    base_idx = index % len(PRODUCT_IMAGES)
    imgs = []
    for i in range(3):
        imgs.append(PRODUCT_IMAGES[(base_idx + i) % len(PRODUCT_IMAGES)])
    return imgs


def seed_data():
    with app.app_context():
        print("=" * 60)
        print("TRACEABLE MARKETPLACE - HANDMADE CERAMIC SEED DATA")
        print("=" * 60)

        print("\n[1/9] Clearing existing data...")
        db.drop_all()
        db.create_all()
        print("   Database cleared and recreated.")

        print("\n[2/9] Creating categories...")
        categories_data = [
            {"name": "Ceramic Vases", "slug": "ceramic-vases", "description": "Hand-thrown and sculpted ceramic vases in various styles"},
            {"name": "Pottery Bowls", "slug": "pottery-bowls", "description": "Handmade bowls for dining, decoration, and ritual use"},
            {"name": "Sculptures", "slug": "sculptures", "description": "Artistic ceramic sculptures and figurines"},
            {"name": "Tableware", "slug": "tableware", "description": "Plates, cups, mugs, and serving pieces"},
            {"name": "Tiles & Mosaics", "slug": "tiles-mosaics", "description": "Hand-painted ceramic tiles and mosaic art"},
            {"name": "Jewelry", "slug": "jewelry", "description": "Ceramic pendants, earrings, and wearable art"},
            {"name": "Home Decor", "slug": "home-decor", "description": "Lamps, planters, and decorative ceramic objects"},
            {"name": "Digital Patterns", "slug": "digital-patterns", "description": "Digital ceramic glaze recipes and pattern designs"},
            {"name": "Kiln Tools", "slug": "kiln-tools", "description": "Tools, stencils, and equipment for ceramic artists"},
            {"name": "Raku & Specialty", "slug": "raku-specialty", "description": "Raku-fired and specialty technique ceramics"},
        ]
        categories = []
        for cat_data in categories_data:
            cat = Category(**cat_data, is_active=True)
            db.session.add(cat)
            categories.append(cat)
        db.session.commit()
        print(f"   Created {len(categories)} categories.")

        print("\n[3/9] Creating users (11 total)...")
        users_data = [
            {"username": "admin", "email": "admin@traceable.market", "password": "admin123", "role": "admin",
             "is_verified": True, "full_name": "System Administrator", "phone": "+1-555-0100",
             "address": "100 Admin Plaza, Tech City, TC 10001", "bio": "Platform administrator and blockchain operator."},
            {"username": "john_doe", "email": "john@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "John Doe", "phone": "+1-555-0101",
             "address": "456 Oak Avenue, New York, NY 10001", "bio": "Ceramic artist specializing in raku firing and Japanese pottery techniques. 15 years of experience."},
            {"username": "jane_smith", "email": "jane@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Jane Smith", "phone": "+1-555-0102",
             "address": "789 Pine Road, Los Angeles, CA 90001", "bio": "Studio potter creating functional stoneware with modern minimalist designs."},
            {"username": "mike_wilson", "email": "mike@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Mike Wilson", "phone": "+1-555-0103",
             "address": "321 Elm Street, Chicago, IL 60601", "bio": "Sculptural ceramic artist. My pieces explore the relationship between form and texture."},
            {"username": "sarah_lee", "email": "sarah@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Sarah Lee", "phone": "+1-555-0104",
             "address": "654 Maple Drive, Houston, TX 77001", "bio": "Traditional Korean ceramicist. I create celadon and buncheong ware using ancient techniques."},
            {"username": "david_chen", "email": "david@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "David Chen", "phone": "+1-555-0105",
             "address": "987 Cedar Lane, Phoenix, AZ 85001", "bio": "Contemporary ceramic jewelry designer. Each piece is hand-formed and one-of-a-kind."},
            {"username": "emma_brown", "email": "emma@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Emma Brown", "phone": "+1-555-0106",
             "address": "147 Birch Way, Philadelphia, PA 19101", "bio": "Tile and mosaic artist. I create hand-painted ceramic murals and decorative tiles."},
            {"username": "alex_taylor", "email": "alex@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Alex Taylor", "phone": "+1-555-0107",
             "address": "258 Spruce Court, San Antonio, TX 78201", "bio": "Digital ceramic pattern designer. I create glaze recipes and firing schedules for sale."},
            {"username": "lisa_garcia", "email": "lisa@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Lisa Garcia", "phone": "+1-555-0108",
             "address": "369 Willow Place, San Diego, CA 92101", "bio": "Mexican Talavera pottery master. Colorful hand-painted traditional designs passed down through generations."},
            {"username": "ryan_martinez", "email": "ryan@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Ryan Martinez", "phone": "+1-555-0109",
             "address": "159 Aspen Boulevard, Dallas, TX 75201", "bio": "Porcelain specialist. Delicate translucent pieces inspired by nature and organic forms."},
            {"username": "olivia_white", "email": "olivia@example.com", "password": "password123", "role": "user",
             "is_verified": True, "full_name": "Olivia White", "phone": "+1-555-0110",
             "address": "753 Redwood Terrace, San Jose, CA 95101", "bio": "Vintage ceramic restorer and collector. I restore antique pieces and sell curated collections."},
        ]

        users = []
        for i, u_data in enumerate(users_data):
            user = User(
                username=u_data["username"],
                email=u_data["email"],
                role=u_data["role"],
                is_verified=u_data["is_verified"],
                is_active=True,
                full_name=u_data["full_name"],
                phone=u_data["phone"],
                address=u_data["address"],
                bio=u_data["bio"],
                profile_image=PROFILE_IMAGES[i % len(PROFILE_IMAGES)],
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90))
            )
            user.set_password(u_data["password"])
            db.session.add(user)
            users.append(user)
        db.session.commit()
        print(f"   Created {len(users)} users.")

        print("\n[4/9] Creating blockchain wallets for all users...")
        wallet_count = 0
        for user in users:
            try:
                wallet_data = generate_wallet()
                wallet = BlockchainWallet(
                    user_id=user.id,
                    address=wallet_data['address'],
                    private_key_encrypted=encrypt_private_key(wallet_data['private_key'])
                )
                db.session.add(wallet)
                wallet_count += 1
            except Exception as e:
                print(f"   Warning: Wallet failed for {user.username}: {e}")
        db.session.commit()
        print(f"   Created {wallet_count} blockchain wallets.")

        print("\n[5/9] Creating handmade ceramic products (minimum 15 per user)...")

        # Handmade ceramic product catalog
        product_catalog = [
            # Ceramic Vases
            ("Ceramic Vases", [
                ("Hand-Thrown Stoneware Vase - Tall", 189.99, "new"),
                ("Raku Fired Ceramic Vase - Copper", 245.00, "new"),
                ("Celadon Glazed Bottle Vase", 320.00, "new"),
                ("Sculptural Organic Form Vase", 450.00, "new"),
                ("Terracotta Amphora Vase", 125.00, "new"),
                ("Crystalline Glaze Statement Vase", 580.00, "new"),
                ("Minimalist White Porcelain Vase", 175.00, "new"),
                ("Vintage Ceramic Floor Vase", 295.00, "used"),
                ("Hand-Painted Talavera Vase", 165.00, "new"),
                ("Wood-Fired Shino Vase", 380.00, "new"),
                ("Nerikomi Patterned Vase", 420.00, "new"),
                ("Saggar Fired Art Vase", 520.00, "new"),
                ("Double-Walled Ceramic Vessel", 290.00, "new"),
                ("Ancient Greek Style Urn", 210.00, "new"),
                ("Teal Reactive Glaze Vase", 145.00, "new"),
            ]),
            # Pottery Bowls
            ("Pottery Bowls", [
                ("Hand-Thrown Ramen Bowl Set", 85.00, "new"),
                ("Large Serving Bowl - Earth Tones", 120.00, "new"),
                ("Matcha Chawan Tea Bowl", 95.00, "new"),
                ("Nested Nesting Bowl Set of 4", 145.00, "new"),
                ("Carved Stoneware Fruit Bowl", 110.00, "new"),
                ("Copper Red Glazed Bowl", 175.00, "new"),
                ("Rustic Farmhouse Mixing Bowl", 65.00, "new"),
                ("Kintsugi Repaired Antique Bowl", 280.00, "used"),
                ("Porcelain Rice Bowl Collection", 75.00, "new"),
                ("Textured Ceramic Soup Bowl", 55.00, "new"),
                ("Hand-Built Ceramic Salad Bowl", 135.00, "new"),
                ("Crystalline Glaze Centerpiece Bowl", 395.00, "new"),
                ("Vintage Studio Pottery Bowl", 150.00, "used"),
                ("Japanese Oribe Green Bowl", 165.00, "new"),
                ("Marbled Clay Decorative Bowl", 95.00, "new"),
            ]),
            # Sculptures
            ("Sculptures", [
                ("Abstract Ceramic Figure Sculpture", 650.00, "new"),
                ("Koi Fish Ceramic Wall Sculpture", 385.00, "new"),
                ("Minimalist Human Form Bust", 520.00, "new"),
                ("Ceramic Bird Family Sculpture", 195.00, "new"),
                ("Abstract Geometric Ceramic Tower", 480.00, "new"),
                ("Hand-Sculpted Dragon Figurine", 320.00, "new"),
                ("Contemporary Ceramic Mask", 275.00, "new"),
                ("Vintage Ceramic Elephant Statue", 180.00, "used"),
                ("Organic Biomorphic Sculpture", 750.00, "new"),
                ("Ceramic Buddha Meditation Figure", 245.00, "new"),
                ("Abstract Female Torso Sculpture", 580.00, "new"),
                ("Whimsical Ceramic Cat Collection", 125.00, "new"),
                ("Large Ceramic Garden Sphere", 420.00, "new"),
                ("Hand-Sculpted Owl Family", 195.00, "new"),
                ("Modernist Ceramic Totem Pole", 890.00, "new"),
            ]),
            # Tableware
            ("Tableware", [
                ("Hand-Thrown Dinner Plate Set of 6", 240.00, "new"),
                ("Artisan Coffee Mug Collection", 45.00, "new"),
                ("Ceramic Tea Cup & Saucer Set", 85.00, "new"),
                ("Handmade Ceramic Pitcher", 95.00, "new"),
                ("Salt & Pepper Shaker Set", 35.00, "new"),
                ("Butter Dish with Lid", 48.00, "new"),
                ("Ceramic Spoon Rest", 28.00, "new"),
                ("Serving Platter - Ocean Blue", 135.00, "new"),
                ("Espresso Cup Set of 4", 68.00, "new"),
                ("Ceramic Gravy Boat", 42.00, "new"),
                ("Hand-Pressed Sushi Plate Set", 155.00, "new"),
                ("Ceramic Wine Coaster Set", 38.00, "new"),
                ("Bread Basket with Warmer", 75.00, "new"),
                ("Ceramic Oil Dispenser Bottle", 52.00, "new"),
                ("Tapas Plate Collection Set", 110.00, "new"),
            ]),
            # Tiles & Mosaics
            ("Tiles & Mosaics", [
                ("Hand-Painted Spanish Tile Set", 180.00, "new"),
                ("Moroccan Zellige Tile Collection", 220.00, "new"),
                ("Ceramic Mosaic Wall Art Panel", 450.00, "new"),
                ("Japanese Wave Pattern Tile Set", 165.00, "new"),
                ("Custom Name Tile Plaque", 85.00, "new"),
                ("Geometric Pattern Tile Backsplash", 380.00, "new"),
                ("Floral Ceramic Trivet Set", 55.00, "new"),
                ("Vintage Portuguese Azulejo Tiles", 295.00, "used"),
                ("Peacock Feather Mosaic Mirror", 520.00, "new"),
                ("Tree of Life Ceramic Wall Hanging", 340.00, "new"),
                ("Mandala Ceramic Coaster Set", 42.00, "new"),
                ("Koi Pond Ceramic Tile Mural", 680.00, "new"),
                ("Art Nouveau Flower Tile Set", 195.00, "new"),
                ("Sun & Moon Ceramic Wall Plaque", 145.00, "new"),
                ("Custom House Number Ceramic Tiles", 75.00, "new"),
            ]),
            # Jewelry
            ("Jewelry", [
                ("Hand-Formed Ceramic Pendant Necklace", 65.00, "new"),
                ("Porcelain Stud Earrings - Gold", 48.00, "new"),
                ("Ceramic Bead Bracelet Set", 55.00, "new"),
                ("Raku Fired Ceramic Ring", 75.00, "new"),
                ("Hand-Painted Ceramic Brooch", 85.00, "new"),
                ("Ceramic Dangle Earrings - Blue", 42.00, "new"),
                ("Porcelain Cuff Bracelet", 95.00, "new"),
                ("Ceramic Anklet with Charms", 38.00, "new"),
                ("Statement Ceramic Choker Necklace", 120.00, "new"),
                ("Miniature Ceramic Pin Collection", 35.00, "new"),
                ("Crystalline Glaze Pendant", 88.00, "new"),
                ("Ceramic Hair Pin Set", 28.00, "new"),
                ("Porcelain Cameo Brooch", 110.00, "new"),
                ("Ceramic Hoop Earrings - Large", 52.00, "new"),
                ("Hand-Sculpted Ceramic Cufflinks", 68.00, "new"),
            ]),
            # Home Decor
            ("Home Decor", [
                ("Ceramic Table Lamp - Turquoise", 245.00, "new"),
                ("Hand-Thrown Planter with Drainage", 68.00, "new"),
                ("Ceramic Candle Holder Set", 45.00, "new"),
                ("Wall-Mounted Ceramic Air Plant Holder", 38.00, "new"),
                ("Large Ceramic Garden Pot", 125.00, "new"),
                ("Ceramic Incense Burner Tower", 55.00, "new"),
                ("Hand-Painted Ceramic Clock", 185.00, "new"),
                ("Ceramic Picture Frame Set", 42.00, "new"),
                ("Sculptural Ceramic Bookends", 95.00, "new"),
                ("Ceramic Desk Organizer Set", 58.00, "new"),
                ("Hanging Ceramic Bird Feeder", 48.00, "new"),
                ("Ceramic Wind Chime", 65.00, "new"),
                ("Hand-Formed Ceramic Knobs Set", 35.00, "new"),
                ("Ceramic Soap Dish & Dispenser", 42.00, "new"),
                ("Decorative Ceramic Wall Sconce", 165.00, "new"),
            ]),
            # Digital Patterns
            ("Digital Patterns", [
                ("Crystalline Glaze Recipe Collection", 25.00, "new"),
                ("Raku Firing Schedule Guide", 18.00, "new"),
                ("Ceramic Glaze Color Chart PDF", 12.00, "new"),
                ("Pottery Throwing Video Course", 45.00, "new"),
                ("Kiln Temperature Log Template", 8.00, "new"),
                ("Ceramic Surface Design Patterns", 22.00, "new"),
                ("Clay Body Recipe Collection", 15.00, "new"),
                ("Pottery Business Pricing Guide", 28.00, "new"),
                ("Ceramic Tool Making Tutorial", 20.00, "new"),
                ("Glaze Chemistry Calculator", 35.00, "new"),
                ("Hand-Building Techniques Video", 38.00, "new"),
                ("Ceramic Studio Setup Guide", 15.00, "new"),
                ("Underglaze Painting Patterns", 18.00, "new"),
                ("Kiln Maintenance Checklist", 10.00, "new"),
                ("Ceramic Photography Guide", 22.00, "new"),
            ]),
            # Kiln Tools
            ("Kiln Tools", [
                ("Hand-Carved Ceramic Stamp Set", 35.00, "new"),
                ("Pottery Rib Tool Collection", 28.00, "new"),
                ("Ceramic Texture Roller Set", 42.00, "new"),
                ("Hand-Thrown Ceramic Water Bowl", 25.00, "new"),
                ("Ceramic Brush Rest & Holder", 18.00, "new"),
                ("Pottery Sponge Holder", 15.00, "new"),
                ("Ceramic Palette for Glaze Mixing", 22.00, "new"),
                ("Hand-Built Tool Caddy", 38.00, "new"),
                ("Ceramic Spray Bottle", 12.00, "new"),
                ("Pottery Trim Tool Rest", 16.00, "new"),
                ("Ceramic Bamboo Brush Set", 45.00, "new"),
                ("Glaze Test Tile Holder", 20.00, "new"),
                ("Ceramic Work Surface Protector", 30.00, "new"),
                ("Hand-Sculpted Kiln God Figurine", 55.00, "new"),
                ("Ceramic Measuring Cup Set", 25.00, "new"),
            ]),
            # Raku & Specialty
            ("Raku & Specialty", [
                ("Raku Fired Tea Bowl - Copper", 185.00, "new"),
                ("Horsehair Raku Decorative Vase", 320.00, "new"),
                ("Naked Raku Sculptural Vessel", 450.00, "new"),
                ("Pit-Fired Ceramic Wall Art", 280.00, "new"),
                ("Soda-Fired Stoneware Jar", 245.00, "new"),
                ("Wood-Fired Ceramic Plate", 165.00, "new"),
                ("Saggar Fired Orb Sculpture", 380.00, "new"),
                ("Obvara Fungal Decorated Bowl", 195.00, "new"),
                ("Copper Matte Raku Vase", 275.00, "new"),
                ("Feather Raku Decorative Plate", 220.00, "new"),
                ("Post-Fire Reduced Ceramic Set", 340.00, "new"),
                ("Raku Moon Jar - Large", 520.00, "new"),
                ("Smoked-Fired Ceramic Mask", 295.00, "new"),
                ("Nerikomi Marbled Vessel", 410.00, "new"),
                ("Double-Fired Crystalline Bowl", 580.00, "new"),
            ]),
        ]

        all_products = []
        product_counter = 1

        # Each regular user creates products
        regular_users = [u for u in users if u.role == "user"]
        for user in regular_users:
            user_products = []
            # Assign 3 categories to each user for variety
            user_categories = random.sample(product_catalog, min(3, len(product_catalog)))

            for cat_name, items in user_categories:
                # Pick 5-7 products from this category
                num_products = random.randint(5, 7)
                selected = random.sample(items, min(num_products, len(items)))

                for item_name, base_price, condition in selected:
                    # Vary price slightly
                    price = round(base_price * random.uniform(0.85, 1.15), 2)
                    code = f"HMP-2026-{product_counter:04d}"
                    
                    # 60% digital, 40% physical - MORE DIGITAL PRODUCTS
                    if cat_name == "Digital Patterns":
                        ptype = "digital"
                    elif cat_name in ["Kiln Tools", "Tiles & Mosaics"]:
                        ptype = random.choice(["digital", "physical"])
                    else:
                        ptype = random.choice(["digital", "digital", "physical"])
                    
                    # Description based on type
                    if ptype == "digital":
                        desc = f"Digital ceramic resource: {item_name}. Instant download after purchase. Includes high-resolution files, detailed instructions, and lifetime updates. Perfect for ceramic artists and studios."
                    else:
                        desc = f"Handmade ceramic piece: {item_name}. Crafted with care using traditional techniques. Each piece is unique with slight variations in glaze and form. Signed by the artist. Includes certificate of authenticity."

                    product = Product(
                        unique_code=code,
                        name=item_name,
                        description=desc,
                        product_type=ptype,
                        category=cat_name,
                        creator_id=user.id,
                        current_owner_id=user.id,
                        is_listed=True,
                        is_approved=True,
                        status="active",
                        current_price=price,
                        original_price=round(price * 1.2, 2),
                        royalty_percentage=5.0,
                        condition=condition,
                        condition_description="Mint condition, never used" if condition == "new" else "Gently used, well cared for with minor signs of handling",
                        image_urls=get_three_images(product_counter - 1),
                        location=random.choice(LOCATIONS) if ptype == "physical" else "Digital Download",
                        created_at=datetime.utcnow() - timedelta(days=random.randint(10, 60)),
                        listed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(product)
                    user_products.append(product)
                    all_products.append(product)
                    product_counter += 1

            db.session.commit()
            print(f"   {user.username}: Created {len(user_products)} products")

        # Admin creates some products too
        admin = users[0]
        admin_products = []
        for cat_name, items in random.sample(product_catalog, 2):
            for item_name, base_price, condition in random.sample(items, 3):
                price = round(base_price * random.uniform(0.9, 1.1), 2)
                code = f"HMP-2026-{product_counter:04d}"
                # Admin also creates more digital
                ptype = random.choice(["digital", "digital", "physical"])
                
                if ptype == "digital":
                    desc = f"Digital ceramic resource: {item_name}. Instant download after purchase. Includes high-resolution files, detailed instructions, and lifetime updates."
                else:
                    desc = f"Platform verified handmade ceramic: {item_name}. Guaranteed authentic artisan piece."
                
                product = Product(
                    unique_code=code,
                    name=item_name,
                    description=desc,
                    product_type=ptype,
                    category=cat_name,
                    creator_id=admin.id,
                    current_owner_id=admin.id,
                    is_listed=True,
                    is_approved=True,
                    status="active",
                    current_price=price,
                    original_price=round(price * 1.2, 2),
                    royalty_percentage=5.0,
                    condition=condition,
                    condition_description="Excellent condition" if condition == "used" else "Brand new from the kiln",
                    image_urls=get_three_images(product_counter - 1),
                    location="Digital Download" if ptype == "digital" else "Jingdezhen, China",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(5, 40)),
                    listed_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
                )
                db.session.add(product)
                admin_products.append(product)
                all_products.append(product)
                product_counter += 1
        db.session.commit()
        print(f"   {admin.username}: Created {len(admin_products)} products")
        print(f"   TOTAL PRODUCTS: {len(all_products)}")

        print("\n[6/9] Creating ownership transfers (buy/sell activity)...")
        transfer_count = 0
        # Create realistic transfer chains
        for i in range(min(50, len(all_products) // 2)):
            product = random.choice(all_products)
            # Only transfer products that haven't been transferred yet
            if product.creator_id == product.current_owner_id and product.status == "active":
                seller = User.query.get(product.current_owner_id)
                # Pick a different buyer
                potential_buyers = [u for u in users if u.id != seller.id]
                if potential_buyers:
                    buyer = random.choice(potential_buyers)
                    sale_price = round(float(product.current_price) * random.uniform(0.9, 1.0), 2)
                    royalty = round(sale_price * 0.05, 2)
                    platform_fee = round(sale_price * 0.03, 2)

                    transfer = OwnershipTransfer(
                        product_id=product.id,
                        from_user_id=seller.id,
                        to_user_id=buyer.id,
                        sale_price=sale_price,
                        royalty_amount=royalty,
                        royalty_percentage=5.0,
                        platform_fee=platform_fee,
                        platform_fee_percentage=3.0,
                        status="completed",
                        transfer_date=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                        completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(5, 25))
                    )
                    db.session.add(transfer)
                    product.current_owner_id = buyer.id
                    product.sold_at = transfer.completed_at
                    transfer_count += 1

        db.session.commit()
        print(f"   Created {transfer_count} ownership transfers.")

        print("\n[7/9] Creating reviews...")
        review_templates = [
            (5, "Absolutely stunning piece!", "The craftsmanship is incredible. You can feel the artist's passion in every detail. Fast shipping and beautiful packaging."),
            (5, "Perfect addition to my collection", "This ceramic piece arrived exactly as described. The glaze is even more beautiful in person. Would buy again!"),
            (4, "Great quality handmade item", "Minor variation in color from photos but that's the beauty of handmade ceramics. Very satisfied."),
            (5, "Verified authentic on blockchain", "The blockchain traceability gives me complete confidence. Beautiful piece, exactly as listed."),
            (5, "Exceptional artisan work", "Professional packaging and quick delivery. The artist even included a handwritten thank you note."),
            (4, "Good value for handmade", "Fair price for the quality of work. Happy to support independent ceramic artists."),
            (5, "Love this ceramic piece!", "Exactly what I was looking for. The images didn't do it justice - it's gorgeous in person."),
            (5, "Outstanding craftsmanship", "Best ceramic purchase I've made. The firing technique is masterful."),
            (4, "Very nice studio pottery", "Quality handmade item, would recommend to fellow ceramic enthusiasts."),
            (5, "Museum quality work", "This piece belongs in a gallery. The artist is incredibly talented."),
        ]

        review_count = 0
        # Find products that have been transferred (purchased)
        purchased_products = db.session.query(Product).filter(Product.current_owner_id != Product.creator_id).all()
        for product in purchased_products[:45]:
            # Get the buyer
            buyer = User.query.get(product.current_owner_id)
            if buyer:
                template = random.choice(review_templates)
                review = Review(
                    product_id=product.id,
                    user_id=buyer.id,
                    rating=template[0],
                    title=template[1],
                    body=template[2],
                    is_approved=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                db.session.add(review)
                review_count += 1
        db.session.commit()
        print(f"   Created {review_count} reviews.")

        print("\n[8/9] Creating messages between users...")
        message_templates = [
            ("Is this piece still available?", "Hi! I'm interested in this ceramic piece. Is it still available for purchase?"),
            ("Question about glaze technique", "Can you tell me more about the glaze technique used? Is it food-safe?"),
            ("Shipping to Europe", "Do you offer international shipping? I'm located in France and would love to purchase this."),
            ("Custom order inquiry", "Would you consider creating a custom piece similar to this? I have specific dimensions in mind."),
            ("Blockchain verification", "Can you share the blockchain verification record for this piece? I want to confirm authenticity."),
            ("Bundle offer", "I'm interested in multiple pieces from your studio. Can we work out a bundle price?"),
            ("Payment method", "Do you accept PayPal or bank transfer for ceramic purchases?"),
            ("Return policy", "What is your return policy if the ceramic piece arrives damaged during shipping?"),
            ("Kiln firing details", "What temperature was this piece fired at? I'm curious about the clay body used."),
            ("Artist signature", "Is this piece signed by the artist? I'd like to verify the provenance."),
        ]

        message_count = 0
        for _ in range(35):
            sender, receiver = random.sample(regular_users, 2)
            template = random.choice(message_templates)
            message = Message(
                sender_id=sender.id,
                receiver_id=receiver.id,
                subject=template[0],
                body=template[1],
                is_read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
            )
            db.session.add(message)
            message_count += 1

            # Sometimes add a reply
            if random.random() > 0.4:
                reply = Message(
                    sender_id=receiver.id,
                    receiver_id=sender.id,
                    subject=f"Re: {template[0]}",
                    body="Thank you for your interest in my ceramics! Yes, the piece is available. All my work is food-safe and fired to cone 6. Let me know if you have any other questions!",
                    is_read=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                db.session.add(reply)
                message_count += 1

        db.session.commit()
        print(f"   Created {message_count} messages.")

        print("\n[9/9] Creating wishlists, announcements, and notifications...")

        # Wishlists
        wishlist_count = 0
        for user in regular_users:
            for _ in range(random.randint(3, 10)):
                product = random.choice(all_products)
                existing = Wishlist.query.filter_by(user_id=user.id, product_id=product.id).first()
                if not existing:
                    wish = Wishlist(user_id=user.id, product_id=product.id)
                    db.session.add(wish)
                    wishlist_count += 1
        db.session.commit()
        print(f"   Created {wishlist_count} wishlist entries.")

        # Announcements
        announcements = [
            Announcement(title="Welcome to Traceable Ceramic Marketplace!",
                        content="Discover authentic handmade ceramics from artists worldwide. Every piece is blockchain-verified for authenticity.",
                        announcement_type="info", is_active=True, created_by=admin.id),
            Announcement(title="Blockchain Verification Now Live",
                        content="All ceramic pieces are now automatically minted on the blockchain. Verify provenance with a simple scan.",
                        announcement_type="feature", is_active=True, created_by=admin.id),
            Announcement(title="Artist Protection Update",
                        content="New artist royalty system ensures creators earn 5% on every resale of their work. Forever.",
                        announcement_type="feature", is_active=True, created_by=admin.id),
            Announcement(title="International Shipping Available",
                        content="We now offer insured international shipping for ceramic pieces with custom protective packaging.",
                        announcement_type="info", is_active=True, created_by=admin.id),
            Announcement(title="Digital Glaze Recipes Added",
                        content="New category for digital ceramic resources including glaze recipes, firing schedules, and tutorials.",
                        announcement_type="feature", is_active=True, created_by=admin.id),
        ]
        for ann in announcements:
            db.session.add(ann)
        db.session.commit()
        print(f"   Created {len(announcements)} announcements.")

        # Notifications
        notif_count = 0
        for user in users:
            if user.role != "admin":
                notifs = [
                    Notification(user_id=user.id, title="Welcome to the Ceramic Community!",
                                message="Start exploring handmade ceramics from verified artists around the world.",
                                notification_type="info", is_read=False),
                    Notification(user_id=user.id, title="Complete Your Artist Profile",
                                message="Add your studio photos and ceramic techniques to attract more buyers.",
                                notification_type="info", is_read=random.choice([True, False])),
                    Notification(user_id=user.id, title="Blockchain Minting Enabled",
                                message="Your ceramic pieces can now be minted on the blockchain for provenance tracking.",
                                notification_type="feature", is_read=random.choice([True, False])),
                ]
                for n in notifs:
                    db.session.add(n)
                    notif_count += 1
        db.session.commit()
        print(f"   Created {notif_count} notifications.")

        # ============== FINAL SUMMARY ==============
        print("\n" + "=" * 60)
        print("SEED DATA CREATION COMPLETE!")
        print("=" * 60)
        print(f"  Users:              {User.query.count()}")
        print(f"  Categories:         {Category.query.count()}")
        print(f"  Products:           {Product.query.count()}")
        print(f"  Ownership Transfers:{OwnershipTransfer.query.count()}")
        print(f"  Reviews:            {Review.query.count()}")
        print(f"  Messages:           {Message.query.count()}")
        print(f"  Wishlists:          {Wishlist.query.count()}")
        print(f"  Announcements:      {Announcement.query.count()}")
        print(f"  Notifications:      {Notification.query.count()}")
        print(f"  Blockchain Wallets: {BlockchainWallet.query.count()}")
        print("=" * 60)

        # Products per user breakdown
        print("\nProducts per user:")
        for user in users:
            count = Product.query.filter_by(creator_id=user.id).count()
            print(f"  {user.username:20s} {count:3d} products")

        # Category breakdown
        print("\nProducts by category:")
        for cat in categories:
            count = Product.query.filter_by(category=cat.name).count()
            print(f"  {cat.name:25s} {count:3d} products")

        print("\n" + "=" * 60)
        print("LOGIN CREDENTIALS")
        print("=" * 60)
        print("  Admin:  admin@traceable.market / admin123")
        print("  Users:  [username]@example.com / password123")
        print("=" * 60)


if __name__ == "__main__":
    seed_data()
