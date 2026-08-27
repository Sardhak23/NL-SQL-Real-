"""
Database Schema Catalog and Sample Natural Language Queries
for the NL-to-SQL Streamlit Prototype.
"""

from typing import Dict, List, Any

# Enterprise Relational Database Schema Catalog
SCHEMA_CATALOG: Dict[str, List[Dict[str, str]]] = {
    "customers": [
        {"name": "customer_id", "type": "INTEGER PRIMARY KEY", "description": "Unique customer identifier"},
        {"name": "company_name", "type": "VARCHAR(255)", "description": "Customer business/company name"},
        {"name": "contact_name", "type": "VARCHAR(100)", "description": "Primary contact person"},
        {"name": "email", "type": "VARCHAR(255)", "description": "Contact email address"},
        {"name": "segment", "type": "VARCHAR(50)", "description": "Enterprise, Mid-Market, SMB"},
        {"name": "tier", "type": "VARCHAR(50)", "description": "Platinum, Gold, Silver, Bronze"},
        {"name": "country", "type": "VARCHAR(100)", "description": "Customer headquarters country"},
        {"name": "lifetime_value", "type": "DECIMAL(12,2)", "description": "Cumulative historical spend in USD"},
        {"name": "created_at", "type": "TIMESTAMP", "description": "Account registration timestamp"}
    ],
    "products": [
        {"name": "product_id", "type": "INTEGER PRIMARY KEY", "description": "Unique product SKU identifier"},
        {"name": "product_name", "type": "VARCHAR(255)", "description": "Commercial product name"},
        {"name": "category", "type": "VARCHAR(100)", "description": "Product category (Cloud, Hardware, AI, Security)"},
        {"name": "unit_price", "type": "DECIMAL(10,2)", "description": "List unit price in USD"},
        {"name": "cost_price", "type": "DECIMAL(10,2)", "description": "Internal cost of goods sold per unit"},
        {"name": "stock_quantity", "type": "INTEGER", "description": "Units available in warehouse"},
        {"name": "reorder_threshold", "type": "INTEGER", "description": "Safety stock threshold triggering reorder"}
    ],
    "orders": [
        {"name": "order_id", "type": "INTEGER PRIMARY KEY", "description": "Unique order transaction identifier"},
        {"name": "customer_id", "type": "INTEGER FOREIGN KEY", "description": "References customers(customer_id)"},
        {"name": "order_date", "type": "DATE", "description": "Date order was submitted"},
        {"name": "status", "type": "VARCHAR(50)", "description": "Completed, Processing, Shipped, Refunded, Cancelled"},
        {"name": "shipping_region", "type": "VARCHAR(50)", "description": "North America, EMEA, APAC, LATAM"},
        {"name": "total_amount", "type": "DECIMAL(12,2)", "description": "Total order gross invoice value in USD"},
        {"name": "payment_method", "type": "VARCHAR(50)", "description": "Credit Card, Wire Transfer, ACH, Corporate Invoice"}
    ],
    "order_items": [
        {"name": "item_id", "type": "INTEGER PRIMARY KEY", "description": "Unique line item identifier"},
        {"name": "order_id", "type": "INTEGER FOREIGN KEY", "description": "References orders(order_id)"},
        {"name": "product_id", "type": "INTEGER FOREIGN KEY", "description": "References products(product_id)"},
        {"name": "quantity", "type": "INTEGER", "description": "Units purchased in this line item"},
        {"name": "unit_price", "type": "DECIMAL(10,2)", "description": "Price per unit at time of purchase"},
        {"name": "discount_rate", "type": "DECIMAL(4,2)", "description": "Discount applied (0.00 to 0.50)"},
        {"name": "subtotal", "type": "DECIMAL(12,2)", "description": "Line total = quantity * unit_price * (1 - discount)"}
    ],
    "monthly_financials": [
        {"name": "month_year", "type": "VARCHAR(7) PRIMARY KEY", "description": "Fiscal month in YYYY-MM format"},
        {"name": "gross_revenue", "type": "DECIMAL(14,2)", "description": "Total completed invoice revenue"},
        {"name": "cogs", "type": "DECIMAL(14,2)", "description": "Total cost of goods sold"},
        {"name": "net_profit", "type": "DECIMAL(14,2)", "description": "Gross revenue minus COGS and operating expenses"},
        {"name": "total_orders", "type": "INTEGER", "description": "Count of successfully completed orders"},
        {"name": "active_customers", "type": "INTEGER", "description": "Distinct active purchasing customers"},
        {"name": "mom_growth_pct", "type": "DECIMAL(5,2)", "description": "Month-over-Month revenue growth percentage"}
    ]
}

# Pre-configured sample natural language prompts
SAMPLE_QUERIES: List[str] = [
    "What were the top 10 products by revenue in 2025?",
    "Show monthly revenue trend for 2025 with growth rates",
    "Who are our top 5 enterprise customers by lifetime spend?",
    "Break down total sales and order volume by shipping region",
    "Which products have low inventory below reorder threshold?",
    "What is the breakdown of order fulfillment statuses?"
]

# Database Schema Entity Relationship Metadata
SCHEMA_RELATIONSHIPS: List[Dict[str, str]] = [
    {"from": "orders.customer_id", "to": "customers.customer_id", "type": "Many-to-One (N:1)"},
    {"from": "order_items.order_id", "to": "orders.order_id", "type": "Many-to-One (N:1)"},
    {"from": "order_items.product_id", "to": "products.product_id", "type": "Many-to-One (N:1)"}
]
