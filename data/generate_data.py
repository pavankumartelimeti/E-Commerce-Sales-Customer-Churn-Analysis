"""
E-Commerce Dataset Generator
Generates realistic synthetic data for the analysis project.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ─── Config ───────────────────────────────────────────────
N_CUSTOMERS = 2000
N_PRODUCTS = 150
N_ORDERS = 15000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Sports", "Beauty", "Books", "Toys"]
REGIONS = ["North", "South", "East", "West", "Central"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet"]
ORDER_STATUSES = ["Delivered", "Returned", "Cancelled", "Pending"]

# ─── Customers ────────────────────────────────────────────
def generate_customers():
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        reg_date = START_DATE + timedelta(days=random.randint(0, 365))
        customers.append({
            "customer_id": f"C{i:04d}",
            "age": random.randint(18, 65),
            "gender": random.choice(["Male", "Female", "Other"]),
            "region": random.choice(REGIONS),
            "registration_date": reg_date.date(),
            "loyalty_tier": random.choice(["Bronze", "Silver", "Gold", "Platinum"]),
        })
    return pd.DataFrame(customers)

# ─── Products ─────────────────────────────────────────────
def generate_products():
    products = []
    for i in range(1, N_PRODUCTS + 1):
        cat = random.choice(CATEGORIES)
        base_price = round(random.uniform(10, 2000), 2)
        products.append({
            "product_id": f"P{i:04d}",
            "product_name": f"{cat} Product {i}",
            "category": cat,
            "base_price": base_price,
            "cost_price": round(base_price * random.uniform(0.4, 0.7), 2),
            "stock_quantity": random.randint(0, 500),
            "supplier": f"Supplier_{random.randint(1,20)}",
        })
    return pd.DataFrame(products)

# ─── Orders ───────────────────────────────────────────────
def generate_orders(customers_df, products_df):
    orders = []
    order_items = []
    order_id = 1

    customer_ids = customers_df["customer_id"].tolist()
    product_ids = products_df["product_id"].tolist()
    price_map = products_df.set_index("product_id")["base_price"].to_dict()

    # Simulate churned customers (bought only in 2022)
    churned = random.sample(customer_ids, int(N_CUSTOMERS * 0.30))

    for _ in range(N_ORDERS):
        cust = random.choice(customer_ids)

        if cust in churned:
            order_date = START_DATE + timedelta(days=random.randint(0, 364))
        else:
            order_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))

        status = np.random.choice(
            ORDER_STATUSES, p=[0.78, 0.10, 0.08, 0.04]
        )
        n_items = random.randint(1, 5)
        prods = random.sample(product_ids, min(n_items, len(product_ids)))

        total = 0
        for prod in prods:
            qty = random.randint(1, 4)
            discount = round(random.uniform(0, 0.30), 2)
            unit_price = price_map[prod]
            line_total = round(unit_price * qty * (1 - discount), 2)
            total += line_total
            order_items.append({
                "order_item_id": f"OI{len(order_items)+1:06d}",
                "order_id": f"ORD{order_id:06d}",
                "product_id": prod,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_pct": discount,
                "line_total": line_total,
            })

        orders.append({
            "order_id": f"ORD{order_id:06d}",
            "customer_id": cust,
            "order_date": order_date.date(),
            "status": status,
            "payment_method": random.choice(PAYMENT_METHODS),
            "total_amount": round(total, 2),
            "shipping_days": random.randint(1, 10) if status == "Delivered" else None,
        })
        order_id += 1

    return pd.DataFrame(orders), pd.DataFrame(order_items)

# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating datasets...")
    customers = generate_customers()
    products = generate_products()
    orders, order_items = generate_orders(customers, products)

    out = os.path.dirname(os.path.abspath(__file__))
    customers.to_csv(f"{out}/customers.csv", index=False)
    products.to_csv(f"{out}/products.csv", index=False)
    orders.to_csv(f"{out}/orders.csv", index=False)
    order_items.to_csv(f"{out}/order_items.csv", index=False)

    print(f"✅ customers.csv     → {len(customers):,} rows")
    print(f"✅ products.csv      → {len(products):,} rows")
    print(f"✅ orders.csv        → {len(orders):,} rows")
    print(f"✅ order_items.csv   → {len(order_items):,} rows")
