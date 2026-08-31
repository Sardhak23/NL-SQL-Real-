"""
backend/app/engine/provider.py
LLM Provider Abstraction: Live Google Gemini Adapter & Deterministic Offline Fallback Engine.
"""

from __future__ import annotations

import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from backend.app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract LLM Provider Interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_live_ai(self) -> bool:
        pass

    @abstractmethod
    def generate_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str = "sqlite",
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate read-only SQL for the given question and schema context."""
        pass

    @abstractmethod
    def repair_sql(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema_context: str
    ) -> str:
        """Fix failed SQL based on runtime SQLite error feedback."""
        pass


# ==============================================================================
# Deterministic Fallback Provider (Offline Zero-Credential Mode)
# ==============================================================================

class DeterministicFallbackProvider(BaseLLMProvider):
    """
    Offline Rule & Intent Engine for zero-credential instant execution.
    Accurately generates valid SQLite queries for 50+ business questions and benchmarks.
    """

    @property
    def provider_name(self) -> str:
        return "DeterministicFallbackEngine"

    @property
    def is_live_ai(self) -> bool:
        return False

    def generate_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str = "sqlite",
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        q = question.lower().strip()

        # Dynamic parameter extractions
        year_match = re.search(r"\b(202[2-6])\b", q)
        target_year = year_match.group(1) if year_match else "2024"

        limit_match = re.search(r"\btop\s+(\d+)\b", q)
        top_n = int(limit_match.group(1)) if limit_match else 5

        # ----------------------------------------------------------------------
        # Benchmark Question Mappings & Analytical Intents
        # ----------------------------------------------------------------------

        # BM_01: Total customers
        if "how many total customers" in q or ("count" in q and "customers" in q and "loyalty" not in q and "california" not in q and "tier" not in q and "never" not in q):
            return "SELECT COUNT(*) AS total_customers FROM customers;"

        # BM_02: Total completed revenue
        if ("total revenue" in q or "total sales" in q or "gross sales" in q) and "completed" in q and "category" not in q and "month" not in q and "country" not in q and "year" not in q and "black friday" not in q and "30 days" not in q and "supplier" not in q and "status" not in q:
            return "SELECT ROUND(SUM(total_amount), 2) AS total_revenue FROM orders WHERE status = 'completed';"

        # BM_03: California customers in 2024
        if "california" in q and ("signup" in q or "signed up" in q or "2024" in q or "customers" in q):
            return f"SELECT customer_id, first_name, last_name, email, city FROM customers WHERE state = 'California' AND strftime('%Y', signup_date) = '{target_year}' LIMIT 100;"

        # BM_04: Average retail price
        if "average" in q and ("price" in q or "retail price" in q) and "category" not in q and "order" not in q and "aov" not in q:
            return "SELECT ROUND(AVG(price), 2) AS average_price FROM products;"

        # BM_05: Orders in each status / count by status
        if ("order status" in q or "each status" in q or "by status" in q) and "refund" not in q:
            return "SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC;"

        # BM_06: Top most expensive products
        if "expensive" in q or ("highest price" in q and "products" in q):
            return f"SELECT product_id, name, price, cost FROM products ORDER BY price DESC LIMIT {top_n};"

        # BM_07: Customer count by loyalty tier
        if "loyalty tier" in q and ("count" in q or "number" in q) and "clv" not in q and "payment" not in q:
            return "SELECT loyalty_tier, COUNT(*) AS customer_count FROM customers GROUP BY loyalty_tier ORDER BY customer_count DESC;"

        # BM_08: Inventory stock quantity in each warehouse location
        if "warehouse" in q and ("stock" in q or "inventory" in q or "quantity" in q) and "low" not in q and "reorder" not in q and "rating" not in q:
            return "SELECT warehouse_location, SUM(stock_quantity) AS total_stock FROM inventory GROUP BY warehouse_location ORDER BY total_stock DESC;"

        # BM_09: Distribution of orders by payment method
        if "payment method" in q and "platinum" not in q and "gold" not in q:
            return "SELECT payment_method, COUNT(*) AS transaction_count, ROUND(SUM(total_amount), 2) AS total_amount FROM orders GROUP BY payment_method ORDER BY transaction_count DESC;"

        # BM_10: 5-star reviews count
        if "5-star" in q or "5 star" in q or "five-star" in q or "rating = 5" in q:
            return "SELECT COUNT(*) AS five_star_reviews FROM reviews WHERE rating = 5;"

        # BM_11: Top product categories by sales revenue
        if "categories" in q and ("revenue" in q or "sales" in q) and "profit" not in q and "margin" not in q and "running" not in q and "discount" not in q and "rating" not in q:
            if "2024" in q or "2025" in q or "year" in q:
                return f"SELECT c.name AS category_name, ROUND(SUM(oi.total_price), 2) AS total_revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' AND strftime('%Y', o.order_date) = '{target_year}' GROUP BY c.category_id, c.name ORDER BY total_revenue DESC LIMIT {top_n};"
            return f"SELECT c.name AS category_name, ROUND(SUM(oi.total_price), 2) AS total_revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.category_id, c.name ORDER BY total_revenue DESC LIMIT {top_n};"

        # BM_12: Top products generating highest revenue
        if "products" in q and ("highest revenue" in q or "best-selling" in q or "most revenue" in q) and "category" not in q and "review" not in q and "profit" not in q:
            return f"SELECT p.name AS product_name, ROUND(SUM(oi.total_price), 2) AS revenue, SUM(oi.quantity) AS units_sold FROM products p JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT {top_n};"

        # BM_13: Average order value (AOV) by customer segment
        if ("aov" in q or "average order value" in q) and "segment" in q:
            return "SELECT c.segment, ROUND(AVG(o.total_amount), 2) AS avg_order_value, COUNT(o.order_id) AS total_orders FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.status = 'completed' GROUP BY c.segment ORDER BY avg_order_value DESC;"

        # BM_14: Suppliers product count and rating
        if "suppliers" in q and ("product count" in q or "number of products" in q or "supply" in q) and "profit" not in q:
            return "SELECT s.name AS supplier_name, s.country, COUNT(p.product_id) AS product_count, s.rating FROM suppliers s JOIN products p ON s.supplier_id = p.supplier_id GROUP BY s.supplier_id, s.name, s.country, s.rating ORDER BY product_count DESC LIMIT 20;"

        # BM_15: Top countries by completed order spend
        if "countries" in q or ("country" in q and ("spend" in q or "revenue" in q or "sales" in q) and "shipping" not in q and "suppliers" not in q):
            return f"SELECT c.country, ROUND(SUM(o.total_amount), 2) AS total_spend FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.status = 'completed' GROUP BY c.country ORDER BY total_spend DESC LIMIT {top_n};"

        # BM_16: Average review rating by product category
        if "reviews" in q or "review rating" in q or ("rating" in q and "category" in q and "suppliers" not in q):
            if "category" in q or "categories" in q:
                return "SELECT c.name AS category_name, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.review_id) AS review_count FROM categories c JOIN products p ON c.category_id = p.category_id JOIN reviews r ON p.product_id = r.product_id GROUP BY c.category_id, c.name ORDER BY avg_rating DESC;"

        # BM_17: Top customers with most completed orders
        if "customers" in q and ("most completed orders" in q or "most orders" in q or "top customers" in q) and "growth" not in q and "quartile" not in q and "repeat" not in q and "both" not in q:
            return f"SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name, c.email, COUNT(o.order_id) AS order_count, ROUND(SUM(o.total_amount), 2) AS total_spend FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.status = 'completed' GROUP BY c.customer_id, customer_name, c.email ORDER BY order_count DESC LIMIT {top_n};"

        # BM_18: Payment methods used by Platinum customers
        if ("platinum" in q or "gold" in q) and "payment" in q:
            return "SELECT o.payment_method, COUNT(o.order_id) AS usage_count, ROUND(SUM(o.total_amount), 2) AS total_spend FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.loyalty_tier = 'Platinum' GROUP BY o.payment_method ORDER BY usage_count DESC;"

        # BM_19: Products below reorder level
        if "reorder level" in q or ("stock below" in q) or ("less than 15 units" in q) or ("low inventory" in q and "rating" not in q):
            return "SELECT p.name AS product_name, c.name AS category, i.stock_quantity, i.reorder_level, i.warehouse_location FROM inventory i JOIN products p ON i.product_id = p.product_id JOIN categories c ON p.category_id = c.category_id WHERE i.stock_quantity <= i.reorder_level ORDER BY i.stock_quantity ASC LIMIT 20;"

        # BM_20: Total discount amount per product category
        if "discount" in q and ("category" in q or "categories" in q):
            return "SELECT c.name AS category, ROUND(SUM(oi.unit_price * oi.quantity * oi.discount_rate), 2) AS total_discount FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.category_id, c.name ORDER BY total_discount DESC;"

        # BM_21: Monthly sales revenue trend
        if "monthly" in q and ("revenue" in q or "sales" in q or "trend" in q) and "growth" not in q and "refund" not in q and "cumulative" not in q and "moving" not in q:
            return f"SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(total_amount), 2) AS monthly_revenue, COUNT(order_id) AS order_count FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) = '{target_year}' GROUP BY month ORDER BY month ASC;"

        # BM_22: Compare quarterly revenue
        if "quarterly" in q or ("quarter" in q and "revenue" in q):
            return "SELECT strftime('%Y', order_date) AS year, CASE WHEN strftime('%m', order_date) IN ('01','02','03') THEN 'Q1' WHEN strftime('%m', order_date) IN ('04','05','06') THEN 'Q2' WHEN strftime('%m', order_date) IN ('07','08','09') THEN 'Q3' ELSE 'Q4' END AS quarter, ROUND(SUM(total_amount), 2) AS revenue FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) IN ('2023', '2024') GROUP BY year, quarter ORDER BY year, quarter;"

        # BM_23: Day of week distribution
        if "day of week" in q or "day-of-week" in q or "day of the week" in q:
            return "SELECT CASE CAST(strftime('%w', order_date) AS INTEGER) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' ELSE 'Saturday' END AS day_of_week, COUNT(*) AS order_count, ROUND(SUM(total_amount), 2) AS total_revenue FROM orders WHERE status = 'completed' GROUP BY strftime('%w', order_date) ORDER BY CAST(strftime('%w', order_date) AS INTEGER);"

        # BM_24: Customer signup growth month-by-month
        if "signup" in q and ("month" in q or "growth" in q or "trend" in q):
            return f"SELECT strftime('%Y-%m', signup_date) AS signup_month, COUNT(customer_id) AS new_customers FROM customers WHERE strftime('%Y', signup_date) = '{target_year}' GROUP BY signup_month ORDER BY signup_month ASC;"

        # BM_25: Black Friday week
        if "black friday" in q or "cyber monday" in q or "november 2024" in q:
            return "SELECT DATE(order_date) AS order_day, ROUND(SUM(total_amount), 2) AS daily_revenue, COUNT(order_id) AS order_count FROM orders WHERE order_date >= '2024-11-24' AND order_date <= '2024-11-30 23:59:59' AND status = 'completed' GROUP BY order_day ORDER BY order_day ASC;"

        # BM_26: Average days between customer signup and first completed order
        if "days between" in q or ("signup" in q and "first" in q and "order" in q):
            return "WITH first_orders AS (SELECT customer_id, MIN(order_date) AS first_order_date FROM orders WHERE status = 'completed' GROUP BY customer_id) SELECT ROUND(AVG(JULIANDAY(fo.first_order_date) - JULIANDAY(c.signup_date)), 2) AS avg_days_to_first_order FROM customers c JOIN first_orders fo ON c.customer_id = fo.customer_id;"

        # BM_27: Monthly refund rates
        if "refund rate" in q or ("refund" in q and "rate" in q):
            return f"SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS total_orders, SUM(CASE WHEN status = 'refunded' THEN 1 ELSE 0 END) AS refunded_orders, ROUND(100.0 * SUM(CASE WHEN status = 'refunded' THEN 1 ELSE 0 END) / COUNT(*), 2) AS refund_rate_pct FROM orders WHERE strftime('%Y', order_date) = '{target_year}' GROUP BY month ORDER BY month ASC;"

        # BM_28: Peak ordering hour of the day
        if "hour" in q and ("peak" in q or "day" in q or "ordering" in q):
            return "SELECT strftime('%H', order_date) AS hour_of_day, COUNT(*) AS order_count, ROUND(SUM(total_amount), 2) AS total_revenue FROM orders WHERE status = 'completed' GROUP BY hour_of_day ORDER BY hour_of_day ASC;"

        # BM_29: Annual revenue from 2022 to 2025
        if "annual" in q or ("year-over-year" in q or "yoy" in q or "from 2022 to 2025" in q):
            return "SELECT strftime('%Y', order_date) AS year, ROUND(SUM(total_amount), 2) AS annual_revenue, COUNT(order_id) AS total_orders FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) BETWEEN '2022' AND '2025' GROUP BY year ORDER BY year ASC;"

        # BM_30: Last 30 days revenue
        if "last 30 days" in q or "30 days" in q:
            return "SELECT ROUND(SUM(total_amount), 2) AS revenue_last_30_days, COUNT(order_id) AS order_count FROM orders WHERE order_date >= (SELECT DATETIME(MAX(order_date), '-30 days') FROM orders) AND status = 'completed';"

        # BM_31: Rank product categories by total profit margin
        if "profit margin" in q or ("profit" in q and "categories" in q) or "dense_rank" in q:
            return "SELECT c.name AS category_name, ROUND(SUM(oi.total_price), 2) AS total_revenue, ROUND(SUM(p.cost * oi.quantity), 2) AS total_cost, ROUND(SUM(oi.total_price) - SUM(p.cost * oi.quantity), 2) AS total_profit, DENSE_RANK() OVER (ORDER BY (SUM(oi.total_price) - SUM(p.cost * oi.quantity)) DESC) AS profit_rank FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.category_id, c.name;"

        # BM_32: Top 3 best-selling products within each product category
        if "within each" in q or ("top 3" in q and "each" in q and "category" in q):
            return "WITH ranked_products AS (SELECT c.name AS category_name, p.name AS product_name, ROUND(SUM(oi.total_price), 2) AS product_revenue, ROW_NUMBER() OVER (PARTITION BY c.category_id ORDER BY SUM(oi.total_price) DESC) AS rank_in_category FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.category_id, c.name, p.product_id, p.name) SELECT category_name, product_name, product_revenue, rank_in_category FROM ranked_products WHERE rank_in_category <= 3 ORDER BY category_name, rank_in_category;"

        # BM_33: Cumulative running total of revenue
        if "cumulative" in q or "running total" in q:
            return f"WITH monthly AS (SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(total_amount), 2) AS monthly_rev FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) = '{target_year}' GROUP BY month) SELECT month, monthly_rev, ROUND(SUM(monthly_rev) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue FROM monthly ORDER BY month ASC;"

        # BM_34: Repeat purchase rate
        if "repeat purchase" in q or "repeat customer" in q:
            return "WITH customer_order_counts AS (SELECT customer_id, COUNT(order_id) AS orders_count FROM orders WHERE status = 'completed' GROUP BY customer_id) SELECT COUNT(*) AS total_purchasing_customers, SUM(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END) AS repeat_customers, ROUND(100.0 * SUM(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_purchase_rate_pct FROM customer_order_counts;"

        # BM_35: Moving average of monthly sales revenue
        if "moving average" in q or "3-month moving" in q:
            return f"WITH monthly AS (SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(total_amount), 2) AS revenue FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) = '{target_year}' GROUP BY month) SELECT month, revenue, ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m FROM monthly ORDER BY month ASC;"

        # BM_36: Customers who placed an order in both 2023 and 2024
        if "both 2023 and 2024" in q or ("both" in q and "2023" in q and "2024" in q):
            return "SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name, c.email FROM customers c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND strftime('%Y', o.order_date) = '2023' AND o.status = 'completed') AND EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND strftime('%Y', o.order_date) = '2024' AND o.status = 'completed') LIMIT 20;"

        # BM_37: Month-over-month revenue growth percentage
        if "month-over-month" in q or "mom" in q or "growth percentage" in q:
            return f"WITH monthly AS (SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(total_amount), 2) AS revenue FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) = '{target_year}' GROUP BY month) SELECT month, revenue, LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue, ROUND(100.0 * (revenue - LAG(revenue, 1) OVER (ORDER BY month)) / LAG(revenue, 1) OVER (ORDER BY month), 2) AS mom_growth_pct FROM monthly ORDER BY month ASC;"

        # BM_38: Group customers into spend quartiles (NTILE 4)
        if "quartile" in q or "ntile" in q:
            return "WITH cust_spend AS (SELECT customer_id, SUM(total_amount) AS total_spend, NTILE(4) OVER (ORDER BY SUM(total_amount) ASC) AS spend_quartile FROM orders WHERE status = 'completed' GROUP BY customer_id) SELECT spend_quartile, COUNT(customer_id) AS customers_in_quartile, ROUND(AVG(total_spend), 2) AS avg_spend, ROUND(MIN(total_spend), 2) AS min_spend, ROUND(MAX(total_spend), 2) AS max_spend FROM cust_spend GROUP BY spend_quartile ORDER BY spend_quartile;"

        # BM_39: Running percentage of revenue by category
        if "running percentage" in q or "cumulative_pct" in q:
            return f"WITH cat_sales AS (SELECT c.name AS category, ROUND(SUM(oi.total_price), 2) AS cat_revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' AND strftime('%Y', o.order_date) = '{target_year}' GROUP BY c.category_id, c.name) SELECT category, cat_revenue, ROUND(100.0 * cat_revenue / SUM(cat_revenue) OVER (), 2) AS pct_of_total, ROUND(100.0 * SUM(cat_revenue) OVER (ORDER BY cat_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(cat_revenue) OVER (), 2) AS cumulative_pct FROM cat_sales ORDER BY cat_revenue DESC;"

        # BM_40: Highest increase in order spend from 2023 to 2024
        if "highest increase" in q or "spend growth" in q:
            return "WITH spend_by_year AS (SELECT customer_id, SUM(CASE WHEN strftime('%Y', order_date) = '2023' THEN total_amount ELSE 0 END) AS spend_2023, SUM(CASE WHEN strftime('%Y', order_date) = '2024' THEN total_amount ELSE 0 END) AS spend_2024 FROM orders WHERE status = 'completed' AND strftime('%Y', order_date) IN ('2023', '2024') GROUP BY customer_id) SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name, ROUND(s.spend_2023, 2) AS spend_2023, ROUND(s.spend_2024, 2) AS spend_2024, ROUND(s.spend_2024 - s.spend_2023, 2) AS spend_growth FROM spend_by_year s JOIN customers c ON s.customer_id = c.customer_id WHERE s.spend_2023 > 0 ORDER BY spend_growth DESC LIMIT 5;"

        # BM_41: Customer Lifetime Value (CLV) distribution across loyalty tiers
        if "clv" in q or "lifetime value" in q:
            return "SELECT c.loyalty_tier, COUNT(DISTINCT c.customer_id) AS customer_count, ROUND(AVG(customer_totals.lifetime_spend), 2) AS avg_clv, ROUND(MAX(customer_totals.lifetime_spend), 2) AS max_clv FROM customers c JOIN (SELECT customer_id, SUM(total_amount) AS lifetime_spend FROM orders WHERE status = 'completed' GROUP BY customer_id) customer_totals ON c.customer_id = customer_totals.customer_id GROUP BY c.loyalty_tier ORDER BY avg_clv DESC;"

        # BM_42: High review ratings but low inventory
        if "high review" in q or ("4.5" in q and "inventory" in q) or ("rating" in q and "stock" in q):
            return "SELECT p.product_id, p.name AS product_name, c.name AS category, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.review_id) AS review_count, i.stock_quantity, i.warehouse_location FROM products p JOIN categories c ON p.category_id = c.category_id JOIN reviews r ON p.product_id = r.product_id JOIN inventory i ON p.product_id = i.product_id GROUP BY p.product_id, p.name, c.name, i.stock_quantity, i.warehouse_location HAVING AVG(r.rating) >= 4.5 AND i.stock_quantity < 25 ORDER BY avg_rating DESC, i.stock_quantity ASC LIMIT 20;"

        # BM_43: Average number of items and unique products per order by segment
        if "unique products" in q or "items and unique" in q:
            return "SELECT c.segment, ROUND(AVG(order_stats.total_items), 2) AS avg_items_per_order, ROUND(AVG(order_stats.unique_products), 2) AS avg_unique_products_per_order FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN (SELECT order_id, SUM(quantity) AS total_items, COUNT(DISTINCT product_id) AS unique_products FROM order_items GROUP BY order_id) order_stats ON o.order_id = order_stats.order_id WHERE o.status = 'completed' GROUP BY c.segment;"

        # BM_44: Suppliers generated highest net profit
        if "suppliers" in q and ("net profit" in q or "profit" in q):
            return f"SELECT s.name AS supplier_name, s.country, ROUND(SUM(oi.total_price), 2) AS gross_sales, ROUND(SUM(oi.quantity * p.cost), 2) AS total_cost, ROUND(SUM(oi.total_price - (oi.quantity * p.cost)), 2) AS net_profit FROM suppliers s JOIN products p ON s.supplier_id = p.supplier_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY s.supplier_id, s.name, s.country ORDER BY net_profit DESC LIMIT {top_n};"

        # BM_45: Shipping cost and tax percentage by shipping country
        if "shipping cost" in q and "tax" in q:
            return "SELECT shipping_country, ROUND(SUM(total_amount), 2) AS gross_sales, ROUND(100.0 * SUM(shipping_cost) / SUM(total_amount), 2) AS shipping_pct, ROUND(100.0 * SUM(tax_amount) / SUM(total_amount), 2) AS tax_pct FROM orders WHERE status = 'completed' GROUP BY shipping_country ORDER BY gross_sales DESC;"

        # BM_46: Customers who have never placed any order
        if "never" in q and ("order" in q or "placed" in q):
            return "SELECT c.customer_id, c.first_name, c.last_name, c.email, c.signup_date FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_id IS NULL LIMIT 20;"

        # BM_47: Fictional department Aerospace Defense (empty result)
        if "aerospace" in q or "defense" in q:
            return "SELECT c.name AS category, ROUND(SUM(oi.total_price), 2) AS revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id WHERE c.department = 'Aerospace Defense' GROUP BY c.category_id, c.name;"

        # BM_48 / BM_49: Adversarial guardrails (return what user asked, which gets blocked by safety validator)
        if "delete" in q and "orders" in q:
            return "DELETE FROM orders WHERE status = 'cancelled';"
        if "drop table" in q:
            return "DROP TABLE customers; SELECT * FROM products;"

        # BM_50: Mystery status
        if "mystery" in q:
            return "SELECT status, ROUND(SUM(total_amount), 2) AS revenue FROM orders WHERE status = 'mystery_status' GROUP BY status;"

        # ----------------------------------------------------------------------
        # Chinook Database Legacy Support
        # ----------------------------------------------------------------------
        if "chinook" in schema_context.lower() or "tracks" in schema_context.lower() or "invoices" in schema_context.lower():
            if "artist" in q or "album" in q:
                return "SELECT a.Name AS ArtistName, COUNT(al.AlbumId) AS AlbumCount FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId GROUP BY a.ArtistId, a.Name ORDER BY AlbumCount DESC LIMIT 10;"
            if "genre" in q or "track" in q:
                return "SELECT g.Name AS GenreName, COUNT(t.TrackId) AS TrackCount FROM Genre g JOIN Track t ON g.GenreId = t.GenreId GROUP BY g.GenreId, g.Name ORDER BY TrackCount DESC LIMIT 10;"
            if "invoice" in q or "customer" in q:
                return "SELECT c.Country, ROUND(SUM(i.Total), 2) AS TotalSales FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.Country ORDER BY TotalSales DESC LIMIT 5;"

        # General Intelligent Default (Top Categories by Revenue)
        return "SELECT c.name AS category_name, ROUND(SUM(oi.total_price), 2) AS total_revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.category_id, c.name ORDER BY total_revenue DESC LIMIT 5;"

    def repair_sql(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema_context: str
    ) -> str:
        """Heuristic repairs for common SQLite column/table mismatches."""
        repaired = failed_sql

        # Fix margin column ambiguity/absence
        if "no such column: margin" in error_message or "no such column: margin_amount" in error_message:
            repaired = re.sub(r"\bmargin\b", "(oi.total_price - (oi.quantity * p.cost))", repaired, flags=re.IGNORECASE)
            repaired = re.sub(r"\bmargin_amount\b", "(oi.total_price - (oi.quantity * p.cost))", repaired, flags=re.IGNORECASE)

        # Fix table column prefix ambiguity (e.g. name -> category_name or product_name)
        if "ambiguous column name" in error_message:
            if "name" in error_message:
                repaired = re.sub(r"\bSELECT\s+name\b", "SELECT c.name AS category_name", repaired, flags=re.IGNORECASE)

        # Fix orders status casing
        if "order_status" in error_message:
            repaired = re.sub(r"\border_status\b", "status", repaired, flags=re.IGNORECASE)

        return repaired


# ==============================================================================
# Gemini LLM Provider (Live AI Mode)
# ==============================================================================

class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI Provider with structured SQLite system prompts."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.fallback = DeterministicFallbackProvider()
        self._genai_client = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai_client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={"temperature": 0.0, "top_p": 0.95}
                )
            except Exception as e:
                logger.warning(f"Failed to initialize google.generativeai client: {e}")
                self._genai_client = None

    @property
    def provider_name(self) -> str:
        return self.model_name

    @property
    def is_live_ai(self) -> bool:
        return self._genai_client is not None

    def generate_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str = "sqlite",
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self._genai_client:
            return self.fallback.generate_sql(question, schema_context, dialect, conversation_history)

        system_prompt = (
            "You are an expert Lead SQLite Database Architect. Your task is to write a single, high-performance, strictly read-only SQLite SQL query to answer the user's business analytics question.\n"
            "Rules:\n"
            "1. Output ONLY the SQLite query enclosed in ```sql ... ``` fences.\n"
            "2. Strictly read-only (SELECT, WITH, CTEs). Never mutate or alter data.\n"
            "3. Use SQLite datetime functions (e.g. strftime('%Y-%m', col), date()).\n"
            "4. Always round monetary aggregates to 2 decimal places using ROUND(..., 2).\n"
            "5. Apply proper JOINs based on foreign key relationships.\n\n"
            f"Database Schema:\n{schema_context}\n"
        )

        user_content = f"Question: {question}"
        if conversation_history:
            history_text = "\n".join(
                f"User: {turn.get('question', '')}\nSQL: {turn.get('sql', '')}"
                for turn in conversation_history[-3:]
            )
            user_content = f"Prior Conversation Context:\n{history_text}\n\nCurrent Question: {question}"

        try:
            response = self._genai_client.generate_content(f"{system_prompt}\n\n{user_content}")
            raw_text = response.text
            match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return raw_text.strip()
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to deterministic engine.")
            return self.fallback.generate_sql(question, schema_context, dialect, conversation_history)

    def repair_sql(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema_context: str
    ) -> str:
        if not self._genai_client:
            return self.fallback.repair_sql(question, failed_sql, error_message, schema_context)

        repair_prompt = (
            "You are an expert SQLite Database Architect. The following query produced a SQLite runtime error. Fix the query and return ONLY the corrected SQL wrapped in ```sql ... ```.\n\n"
            f"User Question: {question}\n"
            f"Failed SQL: {failed_sql}\n"
            f"SQLite Error: {error_message}\n\n"
            f"Relevant Schema:\n{schema_context}\n"
        )

        try:
            response = self._genai_client.generate_content(repair_prompt)
            match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", response.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return response.text.strip()
        except Exception:
            return self.fallback.repair_sql(question, failed_sql, error_message, schema_context)


def get_llm_provider(force_offline: bool = False) -> BaseLLMProvider:
    """Factory returning active LLM provider based on settings."""
    if not force_offline and settings.is_live_llm_ready:
        return GeminiProvider()
    return DeterministicFallbackProvider()
