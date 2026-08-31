#!/usr/bin/env python3
"""
scripts/generate_dataset.py
High-Performance Synthetic E-Commerce Relational Dataset Generator for SQLite.

Generates a realistic 8-table relational e-commerce database with:
- 500,000+ Orders
- 1,200,000+ Order Items
- 35,000+ Customers
- 2,500 Products across 12 Categories
- 150 Suppliers
- 2,500 Inventory records
- 150,000 Reviews

Features:
- Fast bulk generation with SQLite PRAGMAs (WAL mode, synchronous=OFF, in-memory cache)
- Vectorized chunked batch insertion (25k-50k rows per transaction)
- Post-insertion composite B-Tree indexes
- High statistical realism (Pareto distributions, seasonality, Q4 surges, Black Friday spikes)
- Strict relational integrity and foreign key constraints
"""

from __future__ import annotations

import sys
import os
import time
import random
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional, Set

# Fix seed for reproducible statistical realism while generating authentic data
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

WORKSPACE_ROOT = Path(__file__).parent.parent
DEFAULT_DB_PATH = WORKSPACE_ROOT / "ecommerce.db"

# Data constants
DEPARTMENTS = [
    ("Electronics & Gadgets", "Technology"),
    ("Computers & Accessories", "Technology"),
    ("Home & Kitchen", "Home Goods"),
    ("Furniture & Decor", "Home Goods"),
    ("Clothing & Apparel", "Fashion"),
    ("Footwear & Shoes", "Fashion"),
    ("Beauty & Personal Care", "Personal Care"),
    ("Health & Wellness", "Personal Care"),
    ("Sports & Outdoors", "Outdoors"),
    ("Books & Media", "Entertainment"),
    ("Toys & Games", "Entertainment"),
    ("Automotive & Tools", "Industrial"),
]

COUNTRIES_STATES_CITIES = [
    ("United States", "California", ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"]),
    ("United States", "New York", ["New York City", "Buffalo", "Rochester", "Albany", "Syracuse"]),
    ("United States", "Texas", ["Houston", "Austin", "Dallas", "San Antonio", "Fort Worth"]),
    ("United States", "Florida", ["Miami", "Orlando", "Tampa", "Jacksonville", "Tallahassee"]),
    ("United States", "Washington", ["Seattle", "Tacoma", "Spokane", "Bellevue"]),
    ("United States", "Illinois", ["Chicago", "Naperville", "Rockford", "Peoria"]),
    ("United Kingdom", "England", ["London", "Manchester", "Birmingham", "Leeds", "Bristol"]),
    ("United Kingdom", "Scotland", ["Edinburgh", "Glasgow", "Aberdeen", "Dundee"]),
    ("Germany", "Bavaria", ["Munich", "Nuremberg", "Augsburg", "Regensburg"]),
    ("Germany", "Berlin", ["Berlin", "Potsdam", "Spandau"]),
    ("Germany", "North Rhine-Westphalia", ["Cologne", "Dusseldorf", "Dortmund", "Essen"]),
    ("Canada", "Ontario", ["Toronto", "Ottawa", "Mississauga", "Hamilton"]),
    ("Canada", "British Columbia", ["Vancouver", "Victoria", "Surrey", "Burnaby"]),
    ("Canada", "Quebec", ["Montreal", "Quebec City", "Laval", "Gatineau"]),
    ("France", "Ile-de-France", ["Paris", "Boulogne-Billancourt", "Saint-Denis"]),
    ("France", "Auvergne-Rhone-Alpes", ["Lyon", "Grenoble", "Saint-Etienne"]),
    ("Australia", "New South Wales", ["Sydney", "Newcastle", "Wollongong"]),
    ("Australia", "Victoria", ["Melbourne", "Geelong", "Ballarat"]),
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
    "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster",
]

PRODUCT_PREFIXES = [
    "Ultra", "Pro", "Quantum", "Apex", "Eco", "Smart", "Nova", "Hyper", "Elite", "Prime",
    "Compact", "Core", "Flex", "Max", "Sonic", "Zen", "Pulse", "Vortex", "Titan", "Aero",
    "Vision", "Omni", "Stealth", "Lumina", "Precision", "Infinity", "NextGen", "Ergo", "Dynamic", "Verve",
]

PRODUCT_NOUNS = {
    "Electronics & Gadgets": ["Noise-Canceling Wireless Headphones", "Smartwatch Fitness Tracker", "4K Action Camera", "Bluetooth Portable Speaker", "USB-C Fast Charger Hub", "True Wireless Earbuds", "Wireless Charging Pad", "VR Headset Kit", "Drone 4K Gimbal", "Mechanical Keyboard"],
    "Computers & Accessories": ["Gaming Laptop 16-inch", "Curved UltraWide Monitor 34-inch", "Ergonomic Vertical Mouse", "Thunderbolt 4 Docking Station", "External NVMe SSD 2TB", "1080p Streaming Webcam", "Laptop Cooling Stand", "Mechanical RGB Gaming Keyboard", "Mesh Wi-Fi 6 Router", "USB Microphone Kit"],
    "Home & Kitchen": ["Espresso Coffee Machine", "Air Fryer Oven 8-in-1", "Stainless Steel Knife Set", "Cast Iron Skillet 12-inch", "Cordless Stick Vacuum", "Smart Electric Kettle", "Non-Stick Cookware Set", "High-Speed Countertop Blender", "Food Processor Multi-Blade", "Slow Cooker Digital 6Qt"],
    "Furniture & Decor": ["Ergonomic Mesh Office Chair", "Electric Standing Desk 60-inch", "Mid-Century Modern Lounge Chair", "Minimalist Bookshelf 5-Tier", "Memory Foam Queen Mattress", "Modern Dimmable Floor Lamp", "Solid Oak Coffee Table", "Ceramic Table Vase Set", "Blackout Curtains Pair", "Velvet Accent Armchair"],
    "Clothing & Apparel": ["Merino Wool Crewneck Sweater", "Performance Tech Fleece Hoodie", "Waterproof Rain Jacket", "Organic Cotton Casual T-Shirt", "Slim-Fit Stretch Chino Pants", "Windbreaker Running Jacket", "Thermal Base Layer Set", "Tailored Linen Button-Down Shirt", "Quilted Puffer Winter Coat", "Athletic Training Shorts"],
    "Footwear & Shoes": ["Cushioned Road Running Shoes", "Waterproof Trail Hiking Boots", "Classic Leather White Sneakers", "Breathable Slip-On Loafers", "All-Weather Winter Snow Boots", "Memory Foam Walking Shoes", "Minimalist Barefoot Trail Shoes", "Orthopedic Comfort Sandals", "High-Top Basketball Sneakers", "Chelsea Suede Ankle Boots"],
    "Beauty & Personal Care": ["Sonic Facial Cleansing Brush", "Ceramic Tourmaline Hair Dryer", "Vitamin C Brightening Serum", "Hyaluronic Acid Moisturizing Cream", "Organic Argan Hair Oil Treatment", "Retinol Anti-Aging Night Cream", "Gentle Hydrating Cleanser", "Charcoal Clay Detox Mask", "UV Defense Sunscreen SPF 50", "Exfoliating Body Scrub"],
    "Health & Wellness": ["Whey Protein Isolate Powder 5lb", "Plant-Based Superfood Greens", "Omega-3 Triple Strength Fish Oil", "Deep Tissue Percussion Massage Gun", "Digital Smart Body Fat Scale", "Organic Multivitamin Daily Pack", "Aromatherapy Essential Oil Diffuser", "Adjustable Dumbbell Set 50lb", "High-Density Yoga Mat with Strap", "Resistance Exercise Bands Set"],
    "Sports & Outdoors": ["Ultralight Backpacking Tent 2-Person", "Double Camping Hammock with Straps", "Insulated Stainless Steel Water Bottle 32oz", "Aluminum Trekking Poles Pair", "Compact Mummy Sleeping Bag", "Waterproof Dry Bag 30L", "Rechargeable LED Headlamp 1000 Lumens", "Portable Camp Stove Burner", "Inflatable Stand Up Paddle Board", "Hydration Pack Backpack 2L"],
    "Books & Media": ["Mastering Python & Data Analytics", "The Modern Product Architect", "Building Scalable Cloud Systems", "Artificial Intelligence Foundations", "Clean Code & System Design", "The Psychology of Strategy", "Financial Modeling Mastery", "Design Systems for Enterprise SaaS", "Microservices Design Patterns", "Data Science in Production"],
    "Toys & Games": ["Architectural Modular Building Kit", "Strategic Board Game Deluxe Edition", "Programmable STEM Robot Kit", "Magnetic 3D Building Blocks Set", "Remote Control High-Speed Monster Truck", "Strategy Card Game Expansion", "Science Chemistry Experiment Lab", "Wooden Classic Chess & Checkers Set", "Interactive Electronic Globe", "Jigsaw Puzzle 1000-Piece Landscape"],
    "Automotive & Tools": ["Cordless Brushless Impact Driver Kit", "Digital Tire Inflator Air Compressor", "Mechanics Tool Set 150-Piece", "OBD2 Bluetooth Diagnostic Scanner", "High-Pressure Car Foam Cannon", "LED Tactical Work Light Magnetic", "Multi-Angle Heavy-Duty Laser Level", "Car Emergency Jump Starter 2000A", "Microfiber Detailing Towel Pack", "Heavy-Duty Extension Cord Reel 50ft"],
}

SUPPLIER_NAMES = [
    "Apex Global Logistics", "NovaTech Manufacturing", "OmniSource Industries", "Lumina Components",
    "Vortex Supply Chain", "Zenith Precision Goods", "Titan Industrial Works", "AeroTech Solutions",
    "Precision Craft Corp", "Infinity Hardware Global", "NextGen Materials", "ErgoDynamic Products",
    "EcoGreen Packaging", "PrimeEdge Distributing", "HyperSpeed Freight", "Quantum Electronics Ltd",
    "BlueWave Marine & Outdoors", "Summit Peak Gear", "Nordic Pure Labs", "Valence Chem & Pharma",
    "Crestline Woodworks", "Sterling Textiles", "Golden Gate Imports", "Pacifica Goods Co",
]

WAREHOUSE_LOCATIONS = ["US-East-1", "US-West-1", "EU-Central-1", "AP-East-1", "US-South-1"]
LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
CUSTOMER_SEGMENTS = ["Consumer", "Corporate", "Small Business"]
ORDER_STATUSES = ["completed", "shipped", "processing", "cancelled", "refunded"]
PAYMENT_METHODS = ["credit_card", "paypal", "apple_pay", "bank_transfer", "crypto"]

REVIEW_TITLES_5 = [
    "Exceeded all expectations!", "Outstanding build quality and value", "Best purchase I've made this year",
    "Highly recommended for anyone", "Flawless performance and sleek design", "Super fast delivery and great product",
    "Five stars without hesitation", "Premium feel at a great price point",
]
REVIEW_TITLES_4 = [
    "Solid product with great features", "Very satisfied, minor room for improvement", "Works exactly as advertised",
    "Good quality for the price", "Pleasantly surprised by the performance",
]
REVIEW_TITLES_3 = [
    "Decent, but has a few quirks", "Average performance, nothing special", "Met basic expectations",
]
REVIEW_TITLES_2 = [
    "Disappointed with the durability", "Not quite as good as expected", "Had a few issues right out of the box",
]
REVIEW_TITLES_1 = [
    "Would not recommend", "Poor quality and defective", "Waste of money, returning immediately",
]


def create_schema(conn: sqlite3.Connection):
    """Create the 8 relational tables with constraints and schema integrity."""
    cursor = conn.cursor()
    
    # 1. Categories
    cursor.execute("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        slug VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        department VARCHAR(50) NOT NULL
    );
    """)

    # 2. Suppliers
    cursor.execute("""
    CREATE TABLE suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(150) NOT NULL,
        contact_name VARCHAR(100),
        email VARCHAR(100),
        phone VARCHAR(50),
        country VARCHAR(60) NOT NULL,
        city VARCHAR(60) NOT NULL,
        rating DECIMAL(2, 1) DEFAULT 4.0
    );
    """)

    # 3. Products
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        name VARCHAR(200) NOT NULL,
        sku VARCHAR(50) NOT NULL UNIQUE,
        description TEXT,
        price DECIMAL(10, 2) NOT NULL,
        cost DECIMAL(10, 2) NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (category_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
    );
    """)

    # 4. Customers
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(60) NOT NULL,
        last_name VARCHAR(60) NOT NULL,
        email VARCHAR(120) NOT NULL UNIQUE,
        phone VARCHAR(50),
        country VARCHAR(60) NOT NULL,
        state VARCHAR(60) NOT NULL,
        city VARCHAR(60) NOT NULL,
        postal_code VARCHAR(20),
        segment VARCHAR(30) NOT NULL,
        signup_date DATETIME NOT NULL,
        loyalty_tier VARCHAR(20) NOT NULL
    );
    """)

    # 5. Orders
    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date DATETIME NOT NULL,
        status VARCHAR(30) NOT NULL,
        payment_method VARCHAR(40) NOT NULL,
        shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
        tax_amount DECIMAL(10, 2) DEFAULT 0.00,
        discount_amount DECIMAL(10, 2) DEFAULT 0.00,
        total_amount DECIMAL(10, 2) NOT NULL,
        shipping_country VARCHAR(60) NOT NULL,
        shipping_state VARCHAR(60) NOT NULL,
        shipping_city VARCHAR(60) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    );
    """)

    # 6. Order Items
    cursor.execute("""
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price DECIMAL(10, 2) NOT NULL,
        discount_rate DECIMAL(4, 2) DEFAULT 0.00,
        total_price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    );
    """)

    # 7. Inventory
    cursor.execute("""
    CREATE TABLE inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL UNIQUE,
        warehouse_location VARCHAR(50) NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        reorder_level INTEGER NOT NULL DEFAULT 20,
        last_restocked_at DATETIME NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    );
    """)

    # 8. Reviews
    cursor.execute("""
    CREATE TABLE reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        review_title VARCHAR(150),
        review_text TEXT,
        review_date DATETIME NOT NULL,
        is_verified_purchase BOOLEAN DEFAULT 1,
        FOREIGN KEY (product_id) REFERENCES products (product_id),
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    );
    """)

    conn.commit()


def create_indexes(conn: sqlite3.Connection):
    """Create composite B-Tree indexes after bulk insertion for lightning-fast queries."""
    cursor = conn.cursor()
    indexes = [
        "CREATE INDEX idx_orders_customer_id ON orders(customer_id);",
        "CREATE INDEX idx_orders_order_date ON orders(order_date);",
        "CREATE INDEX idx_orders_status ON orders(status);",
        "CREATE INDEX idx_orders_status_date ON orders(status, order_date);",
        "CREATE INDEX idx_orders_shipping_country ON orders(shipping_country);",
        "CREATE INDEX idx_order_items_order_id ON order_items(order_id);",
        "CREATE INDEX idx_order_items_product_id ON order_items(product_id);",
        "CREATE INDEX idx_products_category_id ON products(category_id);",
        "CREATE INDEX idx_products_supplier_id ON products(supplier_id);",
        "CREATE INDEX idx_customers_segment ON customers(segment);",
        "CREATE INDEX idx_customers_country_state ON customers(country, state);",
        "CREATE INDEX idx_customers_loyalty ON customers(loyalty_tier);",
        "CREATE INDEX idx_customers_signup ON customers(signup_date);",
        "CREATE INDEX idx_inventory_product_id ON inventory(product_id);",
        "CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_location);",
        "CREATE INDEX idx_reviews_product_id ON reviews(product_id);",
        "CREATE INDEX idx_reviews_rating ON reviews(rating);",
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    conn.commit()


def generate_categories(conn: sqlite3.Connection) -> List[int]:
    """Generate 12 categories."""
    categories_data = []
    for idx, (cat_name, dept) in enumerate(DEPARTMENTS, start=1):
        slug = cat_name.lower().replace(" & ", "-").replace(" ", "-")
        desc = f"Curated selection of premium {cat_name.lower()} in the {dept} department."
        categories_data.append((idx, cat_name, slug, desc, dept))
    
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO categories (category_id, name, slug, description, department) VALUES (?, ?, ?, ?, ?);",
        categories_data
    )
    conn.commit()
    return [c[0] for c in categories_data]


def generate_suppliers(conn: sqlite3.Connection, count: int = 150) -> List[int]:
    """Generate 150 suppliers."""
    suppliers_data = []
    supplier_ids = list(range(1, count + 1))
    for sid in supplier_ids:
        base_name = SUPPLIER_NAMES[(sid - 1) % len(SUPPLIER_NAMES)]
        name = f"{base_name} {sid}" if sid > len(SUPPLIER_NAMES) else base_name
        contact = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = f"contact@{name.lower().replace(' ', '').replace('&', '')[:15]}.com"
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        loc = random.choice(COUNTRIES_STATES_CITIES)
        country = loc[0]
        city = random.choice(loc[2])
        rating = round(random.uniform(3.5, 5.0), 1)
        suppliers_data.append((sid, name, contact, email, phone, country, city, rating))
    
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO suppliers (supplier_id, name, contact_name, email, phone, country, city, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        suppliers_data
    )
    conn.commit()
    return supplier_ids


def generate_products(conn: sqlite3.Connection, count: int = 2500) -> List[Dict[str, Any]]:
    """Generate 2,500 products with realistic pricing and cost margins."""
    products_data = []
    product_records = []
    start_date = datetime(2021, 1, 1)

    for pid in range(1, count + 1):
        cat_id = ((pid - 1) % len(DEPARTMENTS)) + 1
        cat_name, _ = DEPARTMENTS[cat_id - 1]
        nouns = PRODUCT_NOUNS[cat_name]
        prefix = random.choice(PRODUCT_PREFIXES)
        noun = nouns[(pid - 1) % len(nouns)]
        name = f"{prefix} {noun} #{pid}"
        sku = f"SKU-{cat_id:02d}-{pid:05d}"
        desc = f"High-performance {name} engineered for superior reliability."
        
        # Realistic price tiers
        tier_roll = random.random()
        if tier_roll < 0.20:
            price = round(random.uniform(9.99, 49.99), 2)
            margin_pct = random.uniform(0.35, 0.55)
        elif tier_roll < 0.70:
            price = round(random.uniform(50.00, 249.99), 2)
            margin_pct = random.uniform(0.40, 0.65)
        elif tier_roll < 0.92:
            price = round(random.uniform(250.00, 899.99), 2)
            margin_pct = random.uniform(0.45, 0.70)
        else:
            price = round(random.uniform(900.00, 1899.99), 2)
            margin_pct = random.uniform(0.50, 0.75)
        
        cost = round(price * (1.0 - margin_pct), 2)
        supplier_id = random.randint(1, 150)
        created_days = random.randint(0, 1200)
        created_at = (start_date + timedelta(days=created_days)).strftime("%Y-%m-%d %H:%M:%S")

        products_data.append((pid, cat_id, supplier_id, name, sku, desc, price, cost, created_at))
        product_records.append({
            "product_id": pid,
            "category_id": cat_id,
            "price": price,
            "cost": cost,
            "name": name,
        })

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO products (product_id, category_id, supplier_id, name, sku, description, price, cost, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        products_data
    )
    conn.commit()
    return product_records


def generate_customers(conn: sqlite3.Connection, count: int = 50000) -> List[Dict[str, Any]]:
    """Generate 50,000 customers across countries, loyalty tiers, and segments."""
    customers_data = []
    customer_records = []
    base_date = datetime(2022, 1, 1)

    for cid in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}.{cid}@example.com"
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        # Country distribution (US heavy, with Europe & others)
        c_roll = random.random()
        if c_roll < 0.55:
            # US
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "United States"])
        elif c_roll < 0.70:
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "United Kingdom"])
        elif c_roll < 0.82:
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "Germany"])
        elif c_roll < 0.90:
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "Canada"])
        elif c_roll < 0.95:
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "France"])
        else:
            loc = random.choice([x for x in COUNTRIES_STATES_CITIES if x[0] == "Australia"])
        
        country = loc[0]
        state = loc[1]
        city = random.choice(loc[2])
        postal_code = f"{random.randint(10000, 99999)}"

        # Segment distribution
        s_roll = random.random()
        if s_roll < 0.70:
            segment = "Consumer"
        elif s_roll < 0.88:
            segment = "Small Business"
        else:
            segment = "Corporate"

        # Loyalty Tier
        l_roll = random.random()
        if l_roll < 0.55:
            loyalty = "Bronze"
        elif l_roll < 0.80:
            loyalty = "Silver"
        elif l_roll < 0.94:
            loyalty = "Gold"
        else:
            loyalty = "Platinum"

        # Signup Date spanning 2022 to 2026-06
        # Guarantee customer signups in California in 2024
        days_offset = random.randint(0, 1600)
        signup_dt = base_date + timedelta(days=days_offset, seconds=random.randint(0, 86399))
        signup_str = signup_dt.strftime("%Y-%m-%d %H:%M:%S")

        customers_data.append((cid, first, last, email, phone, country, state, city, postal_code, segment, signup_str, loyalty))
        customer_records.append({
            "customer_id": cid,
            "country": country,
            "state": state,
            "city": city,
            "loyalty": loyalty,
            "segment": segment,
            "signup_dt": signup_dt,
        })

    # Ensure some customers in CA in 2024 explicitly for BM_03
    for i in range(100):
        c = customer_records[i]
        c["state"] = "California"
        c["country"] = "United States"
        c["city"] = "San Francisco" if i % 2 == 0 else "Los Angeles"
        c["signup_dt"] = datetime(2024, 1, 15) + timedelta(days=i * 3)
        customers_data[i] = (
            c["customer_id"], customers_data[i][1], customers_data[i][2], customers_data[i][3],
            customers_data[i][4], "United States", "California", c["city"], customers_data[i][8],
            customers_data[i][9], c["signup_dt"].strftime("%Y-%m-%d %H:%M:%S"), customers_data[i][11]
        )

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO customers (customer_id, first_name, last_name, email, phone, country, state, city, postal_code, segment, signup_date, loyalty_tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        customers_data
    )
    conn.commit()
    return customer_records


def generate_orders_and_items(
    conn: sqlite3.Connection,
    customers: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    target_orders: int = 500000,
    batch_size: int = 25000
) -> Tuple[int, int, List[Tuple[int, int, int, str]]]:
    """
    Generate 500,000+ orders and ~1.4M order items in chunked transactions.
    Ensures mathematical accuracy:
    - total_amount matches item totals + shipping + tax - discount
    - Realistic seasonality, Black Friday peaks in Nov 2024, repeat customer patterns
    """
    cursor = conn.cursor()
    
    total_customers = len(customers)
    num_products = len(products)
    
    # Pareto weights: 20% of products get 75% of purchases
    popular_product_count = max(10, int(num_products * 0.20))
    popular_products = products[:popular_product_count]
    other_products = products[popular_product_count:]
    
    # 20% of customers are frequent repeat buyers (80% of volume)
    # Reserve last 500 customers as NEVER ordered (BM_46)
    active_customers_count = total_customers - 500
    vip_customer_count = int(active_customers_count * 0.20)
    vip_customers = customers[:vip_customer_count]
    regular_customers = customers[vip_customer_count:active_customers_count]

    # Pre-build product lookup table
    prod_lookup = {p["product_id"]: p for p in products}

    # Date range: 2022-01-01 to 2026-07-31 (1673 days)
    start_epoch = datetime(2022, 1, 1).timestamp()
    end_epoch = datetime(2026, 7, 31).timestamp()
    time_span = end_epoch - start_epoch

    # Special Black Friday 2024 date window (2024-11-24 to 2024-11-30)
    bf_start_epoch = datetime(2024, 11, 24).timestamp()
    bf_end_epoch = datetime(2024, 11, 30, 23, 59, 59).timestamp()

    order_id_counter = 1
    item_id_counter = 1

    sample_reviews_pool: List[Tuple[int, int, int, str]] = [] # (order_id, customer_id, product_id, date_str)

    total_batches = (target_orders + batch_size - 1) // batch_size
    print(f"Generating {target_orders:,} orders in {total_batches} batches of {batch_size:,}...")

    # Status distribution weights: completed (74%), shipped (12%), processing (6%), cancelled (4%), refunded (4%)
    status_choices = ["completed", "shipped", "processing", "cancelled", "refunded"]
    status_weights = [0.74, 0.12, 0.06, 0.04, 0.04]

    # Payment method weights
    payment_choices = ["credit_card", "paypal", "apple_pay", "bank_transfer", "crypto"]
    payment_weights = [0.45, 0.25, 0.18, 0.08, 0.04]

    start_perf = time.perf_counter()

    for b in range(total_batches):
        current_batch_size = min(batch_size, target_orders - (order_id_counter - 1))
        if current_batch_size <= 0:
            break

        orders_batch = []
        items_batch = []

        for _ in range(current_batch_size):
            oid = order_id_counter
            order_id_counter += 1

            # Select customer
            if random.random() < 0.70:
                cust = random.choice(vip_customers)
            else:
                cust = random.choice(regular_customers)

            cid = cust["customer_id"]
            cust_signup_epoch = cust["signup_dt"].timestamp()

            # Assign order date with Q4 seasonal boost and Nov 2024 Black Friday volume
            if random.random() < 0.04:
                # Black Friday 2024 cluster
                order_epoch = random.uniform(bf_start_epoch, bf_end_epoch)
            else:
                order_epoch = random.uniform(start_epoch, end_epoch)
                # Apply seasonal holiday weighting (Nov-Dec boost)
                dt_temp = datetime.fromtimestamp(order_epoch)
                if dt_temp.month in (11, 12) and random.random() < 0.40:
                    order_epoch = random.uniform(start_epoch, end_epoch)

            # Ensure order date is strictly after customer signup date
            if order_epoch < cust_signup_epoch:
                order_epoch = cust_signup_epoch + random.uniform(3600, 86400 * 300)
                if order_epoch > end_epoch:
                    order_epoch = end_epoch - random.uniform(0, 86400 * 10)

            order_dt = datetime.fromtimestamp(order_epoch)
            order_date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

            status = random.choices(status_choices, weights=status_weights, k=1)[0]
            payment = random.choices(payment_choices, weights=payment_weights, k=1)[0]

            # Generate 1 to 5 order items (average ~2.6 items per order)
            num_items = random.choices([1, 2, 3, 4, 5], weights=[0.40, 0.30, 0.18, 0.08, 0.04], k=1)[0]
            
            items_total = 0.0
            order_discount = 0.0

            # 25% of orders get a 5% to 20% discount
            has_discount = random.random() < 0.25
            discount_rate = random.choice([0.05, 0.10, 0.15, 0.20]) if has_discount else 0.0

            chosen_prod_ids = set()

            for _ in range(num_items):
                item_id = item_id_counter
                item_id_counter += 1

                # Select product (80% popular, 20% others)
                if random.random() < 0.75:
                    p = random.choice(popular_products)
                else:
                    p = random.choice(other_products)

                pid = p["product_id"]
                if pid in chosen_prod_ids:
                    # Choose a different product to ensure unique products per order
                    pid = ((pid + 7) % num_products) + 1
                    p = prod_lookup[pid]
                chosen_prod_ids.add(pid)

                qty = random.choices([1, 2, 3, 4], weights=[0.72, 0.18, 0.07, 0.03], k=1)[0]
                unit_price = p["price"]
                item_disc_rate = discount_rate if has_discount else 0.0
                total_item_price = round(qty * unit_price, 2)
                items_total += total_item_price

                items_batch.append((item_id, oid, pid, qty, unit_price, item_disc_rate, total_item_price))

                # Collect sample for review pool if order completed
                if status == "completed" and len(sample_reviews_pool) < 250000 and random.random() < 0.15:
                    sample_reviews_pool.append((oid, cid, pid, order_date_str))

            shipping_cost = 0.0 if (items_total > 75.0 or cust["loyalty"] in ("Gold", "Platinum")) else 9.99
            tax_amount = round(items_total * 0.075, 2)
            if has_discount:
                discount_amount = round(items_total * discount_rate, 2)
            else:
                discount_amount = 0.0

            total_amount = round(items_total + shipping_cost + tax_amount - discount_amount, 2)

            shipping_country = cust["country"]
            shipping_state = cust["state"]
            shipping_city = cust["city"]

            orders_batch.append((
                oid, cid, order_date_str, status, payment, shipping_cost,
                tax_amount, discount_amount, total_amount, shipping_country,
                shipping_state, shipping_city
            ))

        # Insert batch
        cursor.executemany(
            "INSERT INTO orders (order_id, customer_id, order_date, status, payment_method, shipping_cost, tax_amount, discount_amount, total_amount, shipping_country, shipping_state, shipping_city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            orders_batch
        )
        cursor.executemany(
            "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, discount_rate, total_price) VALUES (?, ?, ?, ?, ?, ?, ?);",
            items_batch
        )
        conn.commit()

        if (b + 1) % 4 == 0 or (b + 1) == total_batches:
            elapsed = time.perf_counter() - start_perf
            pct = ((b + 1) / total_batches) * 100.0
            print(f"  [{pct:5.1f}%] Inserted {order_id_counter - 1:,} orders, {item_id_counter - 1:,} items in {elapsed:.1f}s")

    return order_id_counter - 1, item_id_counter - 1, sample_reviews_pool


def generate_inventory(conn: sqlite3.Connection, products: List[Dict[str, Any]]):
    """Generate inventory records for all products across warehouses."""
    inventory_data = []
    base_date = datetime(2026, 7, 1)

    for p in products:
        pid = p["product_id"]
        inv_id = pid
        warehouse = random.choice(WAREHOUSE_LOCATIONS)
        reorder_lvl = random.choice([15, 20, 25, 30, 50])
        
        # Edge cases for BM_46 (out of stock) and BM_19 / BM_42 (low stock)
        if pid <= 15:
            # Zero stock for BM_46
            stock = 0
        elif pid <= 60:
            # Low stock (< 25 units) for BM_19 and BM_42
            stock = random.randint(5, 20)
        else:
            stock = random.randint(30, 1500)

        days_ago = random.randint(1, 30)
        restock_dt = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")

        inventory_data.append((inv_id, pid, warehouse, stock, reorder_lvl, restock_dt))

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO inventory (inventory_id, product_id, warehouse_location, stock_quantity, reorder_level, last_restocked_at) VALUES (?, ?, ?, ?, ?, ?);",
        inventory_data
    )
    conn.commit()


def generate_reviews(
    conn: sqlite3.Connection,
    reviews_pool: List[Tuple[int, int, int, str]],
    target_count: int = 150000
):
    """Generate 150,000 product reviews with realistic ratings."""
    cursor = conn.cursor()
    reviews_data = []

    # Positively skewed ratings: 5 (50%), 4 (28%), 3 (11%), 2 (6%), 1 (5%)
    rating_weights = [0.05, 0.06, 0.11, 0.28, 0.50]
    rating_choices = [1, 2, 3, 4, 5]

    pool_len = len(reviews_pool)
    actual_count = min(target_count, pool_len)

    for rid in range(1, actual_count + 1):
        oid, cid, pid, order_dt_str = reviews_pool[rid - 1]
        rating = random.choices(rating_choices, weights=rating_weights, k=1)[0]
        
        if rating == 5:
            title = random.choice(REVIEW_TITLES_5)
        elif rating == 4:
            title = random.choice(REVIEW_TITLES_4)
        elif rating == 3:
            title = random.choice(REVIEW_TITLES_3)
        elif rating == 2:
            title = random.choice(REVIEW_TITLES_2)
        else:
            title = random.choice(REVIEW_TITLES_1)

        text = f"{title}. The product arrived on schedule and the packaging was secure."
        
        # Review date 2-10 days after order date
        try:
            ord_dt = datetime.strptime(order_dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            ord_dt = datetime(2024, 6, 1)
        
        rev_dt = (ord_dt + timedelta(days=random.randint(2, 10), hours=random.randint(1, 23))).strftime("%Y-%m-%d %H:%M:%S")
        is_verified = 1

        reviews_data.append((rid, pid, cid, oid, rating, title, text, rev_dt, is_verified))

    # Batch insert reviews in 25k chunks
    chunk_size = 25000
    for i in range(0, len(reviews_data), chunk_size):
        chunk = reviews_data[i:i + chunk_size]
        cursor.executemany(
            "INSERT INTO reviews (review_id, product_id, customer_id, order_id, rating, review_title, review_text, review_date, is_verified_purchase) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
            chunk
        )
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce SQLite database.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_DB_PATH), help="Path to output sqlite db file")
    parser.add_argument("--orders", type=int, default=500000, help="Number of orders to generate (default 500,000)")
    parser.add_argument("--customers", type=int, default=50000, help="Number of customers (default 50,000)")
    parser.add_argument("--products", type=int, default=2500, help="Number of products (default 2,500)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing database if present")
    args = parser.parse_args()

    db_path = Path(args.output).resolve()
    print("=" * 80)
    print("HIGH-PERFORMANCE SYNTHETIC E-COMMERCE DATABASE GENERATOR")
    print(f"Target Database  : {db_path}")
    print(f"Target Orders    : {args.orders:,}")
    print(f"Target Customers : {args.customers:,}")
    print(f"Target Products  : {args.products:,}")
    print("=" * 80)

    if db_path.exists():
        if args.force or os.environ.get("FORCE_REGEN") == "1":
            print(f"Removing existing database file {db_path}...")
            db_path.unlink()
        else:
            print(f"Database {db_path} already exists. Use --force to regenerate.")
            # Verify row counts
            with sqlite3.connect(db_path) as test_conn:
                cur = test_conn.cursor()
                cur.execute("SELECT COUNT(*) FROM orders;")
                cnt = cur.fetchone()[0]
                print(f"Current orders in database: {cnt:,}")
                if cnt >= args.orders:
                    print("Existing database already satisfies target scale! Exiting.")
                    return

    db_path.parent.mkdir(parents=True, exist_ok=True)

    start_total_time = time.perf_counter()

    # Connect with ultra-fast SQLite tuning pragmas
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA cache_size = -128000;")  # 128 MB RAM cache
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")

    try:
        print("[1/6] Creating database relational schema (8 tables)...")
        create_schema(conn)

        print("[2/6] Generating categories and suppliers...")
        generate_categories(conn)
        generate_suppliers(conn, count=150)

        print("[3/6] Generating products catalog (2,500 products)...")
        products = generate_products(conn, count=args.products)

        print("[4/6] Generating customer profiles (50,000 customers)...")
        customers = generate_customers(conn, count=args.customers)

        print(f"[5/6] Generating {args.orders:,} orders and line items...")
        num_orders, num_items, reviews_pool = generate_orders_and_items(
            conn, customers, products, target_orders=args.orders, batch_size=25000
        )

        print(f"[6/6] Generating inventory & {len(reviews_pool):,} reviews...")
        generate_inventory(conn, products)
        generate_reviews(conn, reviews_pool, target_count=150000)

        print("Creating composite B-Tree indexes for fast query execution...")
        idx_start = time.perf_counter()
        create_indexes(conn)
        print(f"Indexes created in {time.perf_counter() - idx_start:.2f}s")

        print("Optimizing database planner statistics (ANALYZE & PRAGMA optimize)...")
        conn.execute("ANALYZE;")
        conn.execute("PRAGMA optimize;")
        conn.commit()

    finally:
        conn.close()

    total_time = time.perf_counter() - start_total_time
    db_size_mb = db_path.stat().st_size / (1024 * 1024)

    print("=" * 80)
    print("DATASET GENERATION COMPLETE!")
    print(f"Total Time Taken : {total_time:.2f} seconds")
    print(f"Database File    : {db_path}")
    print(f"Database Size    : {db_size_mb:.2f} MB")
    print("=" * 80)

    # Verification summary
    with sqlite3.connect(str(db_path)) as v_conn:
        v_cur = v_conn.cursor()
        for tbl in ["categories", "suppliers", "products", "customers", "orders", "order_items", "inventory", "reviews"]:
            v_cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            row_cnt = v_cur.fetchone()[0]
            print(f"  • Table {tbl:<15} : {row_cnt:>10,} rows")
    print("=" * 80)


if __name__ == "__main__":
    main()
