"""
E-Commerce Exploratory Data Analysis (EDA)
Covers: Revenue trends, customer behavior, product performance, churn signals
Run: python eda.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import os
import warnings

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "../data")
OUT  = os.path.join(BASE, "outputs")
DB   = os.path.join(BASE, "ecommerce.db")
os.makedirs(OUT, exist_ok=True)

PALETTE = ["#0D47A1", "#1565C0", "#1976D2", "#42A5F5", "#90CAF9"]
plt.rcParams.update({"figure.dpi": 130, "font.family": "DejaVu Sans"})

# ── Load Data ─────────────────────────────────────────────────
def load_data():
    customers  = pd.read_csv(f"{DATA}/customers.csv",   parse_dates=["registration_date"])
    products   = pd.read_csv(f"{DATA}/products.csv")
    orders     = pd.read_csv(f"{DATA}/orders.csv",      parse_dates=["order_date"])
    order_items= pd.read_csv(f"{DATA}/order_items.csv")
    return customers, products, orders, order_items

# ── Load into SQLite ───────────────────────────────────────────
def load_sqlite(customers, products, orders, order_items):
    conn = sqlite3.connect(DB)
    customers.to_sql("customers",   conn, if_exists="replace", index=False)
    products.to_sql("products",     conn, if_exists="replace", index=False)
    orders.to_sql("orders",         conn, if_exists="replace", index=False)
    order_items.to_sql("order_items",conn,if_exists="replace", index=False)
    print("✅ SQLite DB created:", DB)
    return conn

# ── 1. Revenue Trend ──────────────────────────────────────────
def plot_revenue_trend(conn):
    df = pd.read_sql("""
        SELECT strftime('%Y-%m', order_date) AS month,
               ROUND(SUM(total_amount), 2)   AS revenue,
               COUNT(DISTINCT order_id)       AS orders
        FROM orders WHERE status='Delivered'
        GROUP BY month ORDER BY month
    """, conn)

    fig, ax1 = plt.subplots(figsize=(13, 4))
    ax2 = ax1.twinx()
    ax1.bar(df["month"], df["revenue"], color=PALETTE[2], alpha=0.75, label="Revenue")
    ax2.plot(df["month"], df["orders"], color="#E53935", linewidth=2, marker="o", ms=4, label="Orders")
    ax1.set_title("Monthly Revenue & Order Volume (Delivered)", fontsize=14, fontweight="bold", pad=12)
    ax1.set_xlabel("Month"); ax1.set_ylabel("Revenue (₹)", color=PALETTE[1])
    ax2.set_ylabel("Orders", color="#E53935")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x/1e6:.1f}M"))
    ax1.set_xticks(range(0, len(df), 3))
    ax1.set_xticklabels(df["month"].iloc[::3], rotation=45, ha="right", fontsize=8)
    fig.legend(loc="upper left", bbox_to_anchor=(0.08, 0.88))
    plt.tight_layout()
    plt.savefig(f"{OUT}/01_revenue_trend.png"); plt.close()
    print("📊 Revenue trend saved.")

# ── 2. Category Revenue ───────────────────────────────────────
def plot_category_revenue(conn):
    df = pd.read_sql("""
        SELECT p.category, ROUND(SUM(oi.line_total),2) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o   ON oi.order_id   = o.order_id
        WHERE o.status='Delivered'
        GROUP BY p.category ORDER BY revenue DESC
    """, conn)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(df["category"], df["revenue"], color=PALETTE)
    ax.bar_label(bars, labels=[f"₹{v/1e6:.2f}M" for v in df["revenue"]], padding=5, fontsize=9)
    ax.set_title("Revenue by Product Category", fontsize=13, fontweight="bold")
    ax.set_xlabel("Revenue (₹)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x/1e6:.1f}M"))
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f"{OUT}/02_category_revenue.png"); plt.close()
    print("📊 Category revenue saved.")

# ── 3. RFM Distribution ───────────────────────────────────────
def plot_rfm(conn):
    df = pd.read_sql("""
        SELECT customer_id,
               JULIANDAY('2024-12-31') - JULIANDAY(MAX(order_date)) AS recency,
               COUNT(DISTINCT order_id)                              AS frequency,
               ROUND(SUM(total_amount), 2)                          AS monetary
        FROM orders WHERE status='Delivered'
        GROUP BY customer_id
    """, conn)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col, title, color in zip(
        axes,
        ["recency", "frequency", "monetary"],
        ["Recency (days since last order)", "Frequency (orders)", "Monetary Value (₹)"],
        ["#1976D2", "#43A047", "#FB8C00"]
    ):
        ax.hist(df[col], bins=30, color=color, edgecolor="white", alpha=0.85)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel(col.capitalize())
        ax.set_ylabel("# Customers")
        ax.axvline(df[col].median(), color="red", linestyle="--", linewidth=1.5, label=f"Median: {df[col].median():.0f}")
        ax.legend(fontsize=8)

    plt.suptitle("RFM Distribution — Customer Behavior Analysis", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUT}/03_rfm_distribution.png", bbox_inches="tight"); plt.close()
    print("📊 RFM distribution saved.")

# ── 4. Churn Rate by Region ────────────────────────────────────
def plot_churn_by_region(conn):
    df = pd.read_sql("""
        SELECT c.region,
               COUNT(DISTINCT c.customer_id) AS total,
               SUM(CASE WHEN JULIANDAY('2024-12-31') - JULIANDAY(o.last_order) > 180
                        THEN 1 ELSE 0 END) AS churned
        FROM customers c
        LEFT JOIN (
            SELECT customer_id, MAX(order_date) AS last_order
            FROM orders WHERE status='Delivered' GROUP BY customer_id
        ) o ON c.customer_id = o.customer_id
        GROUP BY c.region
    """, conn)
    df["churn_rate"] = (df["churned"] / df["total"] * 100).round(1)

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(df["region"], df["churn_rate"], color=["#E53935" if r > df["churn_rate"].mean() else "#1976D2"
                                                          for r in df["churn_rate"]])
    ax.bar_label(bars, labels=[f"{v}%" for v in df["churn_rate"]], padding=4, fontsize=10)
    ax.axhline(df["churn_rate"].mean(), color="orange", linestyle="--", linewidth=1.5,
               label=f"Avg: {df['churn_rate'].mean():.1f}%")
    ax.set_title("Customer Churn Rate by Region\n(No purchase in last 180 days)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Churn Rate (%)"); ax.set_ylim(0, df["churn_rate"].max() + 10)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUT}/04_churn_by_region.png"); plt.close()
    print("📊 Churn by region saved.")

# ── 5. Order Status Breakdown ─────────────────────────────────
def plot_order_status(conn):
    df = pd.read_sql("""
        SELECT status, COUNT(*) AS count FROM orders GROUP BY status
    """, conn)

    colors = {"Delivered": "#43A047", "Cancelled": "#E53935",
              "Returned": "#FB8C00", "Pending": "#9E9E9E"}
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        df["count"], labels=df["status"], autopct="%1.1f%%",
        colors=[colors.get(s, "#1976D2") for s in df["status"]],
        startangle=90, pctdistance=0.82,
        wedgeprops=dict(edgecolor="white", linewidth=2)
    )
    for t in autotexts: t.set_fontsize(11); t.set_fontweight("bold")
    ax.set_title("Order Status Distribution", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUT}/05_order_status.png"); plt.close()
    print("📊 Order status saved.")

# ── 6. Payment Method Preference ──────────────────────────────
def plot_payment_methods(conn):
    df = pd.read_sql("""
        SELECT payment_method,
               COUNT(*) AS transactions,
               ROUND(AVG(total_amount), 2) AS aov
        FROM orders WHERE status='Delivered'
        GROUP BY payment_method ORDER BY transactions DESC
    """, conn)

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()
    x = range(len(df))
    ax1.bar(x, df["transactions"], color=PALETTE[1], alpha=0.8, label="Transactions")
    ax2.plot(x, df["aov"], color="#E53935", marker="D", linewidth=2, label="Avg Order Value")
    ax1.set_xticks(x); ax1.set_xticklabels(df["payment_method"], rotation=15)
    ax1.set_ylabel("Transactions"); ax2.set_ylabel("Avg Order Value (₹)")
    ax1.set_title("Payment Method: Volume vs Avg Order Value", fontsize=12, fontweight="bold")
    fig.legend(loc="upper right", bbox_to_anchor=(0.92, 0.88))
    plt.tight_layout()
    plt.savefig(f"{OUT}/06_payment_methods.png"); plt.close()
    print("📊 Payment methods saved.")

# ── Summary Stats ─────────────────────────────────────────────
def print_summary(conn):
    stats = pd.read_sql("""
        SELECT
          COUNT(DISTINCT customer_id)   AS customers,
          COUNT(DISTINCT order_id)      AS total_orders,
          ROUND(SUM(total_amount),2)    AS gross_revenue,
          ROUND(AVG(total_amount),2)    AS aov
        FROM orders WHERE status='Delivered'
    """, conn).iloc[0]

    print("\n" + "="*50)
    print("   📦 E-COMMERCE PROJECT — KEY METRICS")
    print("="*50)
    print(f"   Customers:      {int(stats['customers']):,}")
    print(f"   Orders:         {int(stats['total_orders']):,}")
    print(f"   Gross Revenue:  ₹{stats['gross_revenue']:,.2f}")
    print(f"   Avg Order Value:₹{stats['aov']:,.2f}")
    print("="*50 + "\n")

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Loading data...")
    customers, products, orders, order_items = load_data()
    conn = load_sqlite(customers, products, orders, order_items)

    print("📈 Running analysis...\n")
    print_summary(conn)
    plot_revenue_trend(conn)
    plot_category_revenue(conn)
    plot_rfm(conn)
    plot_churn_by_region(conn)
    plot_order_status(conn)
    plot_payment_methods(conn)

    conn.close()
    print(f"\n✅ All charts saved to: {OUT}/")
    print("📁 SQLite DB ready for Power BI: ecommerce.db\n")
