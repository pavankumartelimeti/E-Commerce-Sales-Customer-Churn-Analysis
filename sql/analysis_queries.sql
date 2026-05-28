-- ============================================================
-- E-Commerce Data Analysis — SQL Queries
-- Database: SQLite / PostgreSQL / MySQL compatible
-- Author: [Your Name] | Project: E-Commerce Analysis
-- ============================================================


-- ── SCHEMA SETUP ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,
    age             INTEGER,
    gender          TEXT,
    region          TEXT,
    registration_date DATE,
    loyalty_tier    TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    base_price      REAL,
    cost_price      REAL,
    stock_quantity  INTEGER,
    supplier        TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT,
    order_date      DATE,
    status          TEXT,
    payment_method  TEXT,
    total_amount    REAL,
    shipping_days   INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   TEXT PRIMARY KEY,
    order_id        TEXT,
    product_id      TEXT,
    quantity        INTEGER,
    unit_price      REAL,
    discount_pct    REAL,
    line_total      REAL,
    FOREIGN KEY (order_id)    REFERENCES orders(order_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);


-- ── 1. REVENUE OVERVIEW ──────────────────────────────────────

-- Monthly Revenue Trend
SELECT
    strftime('%Y-%m', order_date)   AS month,
    COUNT(DISTINCT order_id)        AS total_orders,
    ROUND(SUM(total_amount), 2)     AS gross_revenue,
    ROUND(AVG(total_amount), 2)     AS avg_order_value
FROM orders
WHERE status = 'Delivered'
GROUP BY month
ORDER BY month;


-- Year-over-Year Revenue Comparison
SELECT
    strftime('%Y', order_date)          AS year,
    ROUND(SUM(total_amount), 2)         AS total_revenue,
    COUNT(DISTINCT order_id)            AS orders_count,
    COUNT(DISTINCT customer_id)         AS unique_customers
FROM orders
WHERE status = 'Delivered'
GROUP BY year
ORDER BY year;


-- ── 2. CUSTOMER ANALYSIS ─────────────────────────────────────

-- Customer Lifetime Value (CLV) — Top 20
SELECT
    c.customer_id,
    c.region,
    c.loyalty_tier,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    ROUND(SUM(o.total_amount), 2)       AS lifetime_value,
    ROUND(AVG(o.total_amount), 2)       AS avg_order_value,
    MIN(o.order_date)                   AS first_order,
    MAX(o.order_date)                   AS last_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_id, c.region, c.loyalty_tier
ORDER BY lifetime_value DESC
LIMIT 20;


-- RFM Segmentation (Recency, Frequency, Monetary)
WITH rfm_base AS (
    SELECT
        customer_id,
        JULIANDAY('2024-12-31') - JULIANDAY(MAX(order_date)) AS recency_days,
        COUNT(DISTINCT order_id)                              AS frequency,
        ROUND(SUM(total_amount), 2)                          AS monetary
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT *,
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 90  THEN 4
            WHEN recency_days <= 180 THEN 3
            WHEN recency_days <= 365 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN frequency >= 20 THEN 5
            WHEN frequency >= 10 THEN 4
            WHEN frequency >= 5  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE 1
        END AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Potential Loyalists'
        WHEN r_score >= 4                         THEN 'Recent Customers'
        WHEN f_score >= 4                         THEN 'At Risk'
        ELSE 'Churned'
    END AS customer_segment
FROM rfm_scored
ORDER BY rfm_total DESC;


-- Churn Rate by Region & Loyalty Tier
WITH last_order AS (
    SELECT customer_id, MAX(order_date) AS last_purchase
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
)
SELECT
    c.region,
    c.loyalty_tier,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN JULIANDAY('2024-12-31') - JULIANDAY(lo.last_purchase) > 180
             THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(
        100.0 * SUM(CASE WHEN JULIANDAY('2024-12-31') - JULIANDAY(lo.last_purchase) > 180
                         THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS churn_rate_pct
FROM customers c
LEFT JOIN last_order lo ON c.customer_id = lo.customer_id
GROUP BY c.region, c.loyalty_tier
ORDER BY churn_rate_pct DESC;


-- ── 3. PRODUCT PERFORMANCE ───────────────────────────────────

-- Top 10 Products by Revenue
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity)                        AS units_sold,
    ROUND(SUM(oi.line_total), 2)            AS total_revenue,
    ROUND(SUM(oi.line_total) - SUM(oi.quantity * p.cost_price), 2) AS gross_profit,
    ROUND(100.0 * (SUM(oi.line_total) - SUM(oi.quantity * p.cost_price))
          / NULLIF(SUM(oi.line_total), 0), 2) AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o    ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;


-- Category Sales Mix
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)          AS orders,
    ROUND(SUM(oi.line_total), 2)        AS revenue,
    ROUND(100.0 * SUM(oi.line_total) /
          SUM(SUM(oi.line_total)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(oi.discount_pct) * 100, 2) AS avg_discount_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY revenue DESC;


-- Low Stock Alert (Inventory at Risk)
SELECT
    product_id,
    product_name,
    category,
    stock_quantity,
    CASE
        WHEN stock_quantity = 0   THEN 'OUT OF STOCK'
        WHEN stock_quantity <= 20 THEN 'CRITICAL'
        WHEN stock_quantity <= 50 THEN 'LOW'
        ELSE 'OK'
    END AS stock_status
FROM products
WHERE stock_quantity <= 50
ORDER BY stock_quantity ASC;


-- ── 4. REGIONAL & PAYMENT ANALYSIS ──────────────────────────

-- Revenue by Region
SELECT
    c.region,
    COUNT(DISTINCT o.order_id)      AS orders,
    COUNT(DISTINCT c.customer_id)   AS customers,
    ROUND(SUM(o.total_amount), 2)   AS revenue,
    ROUND(AVG(o.total_amount), 2)   AS aov
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'Delivered'
GROUP BY c.region
ORDER BY revenue DESC;


-- Payment Method Preference
SELECT
    payment_method,
    COUNT(*)                        AS transactions,
    ROUND(SUM(total_amount), 2)     AS revenue,
    ROUND(AVG(total_amount), 2)     AS avg_order_value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS usage_pct
FROM orders
WHERE status = 'Delivered'
GROUP BY payment_method
ORDER BY transactions DESC;


-- ── 5. OPERATIONAL METRICS ───────────────────────────────────

-- Order Fulfillment & Return Analysis
SELECT
    status,
    COUNT(*)                                AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(total_amount), 2)             AS avg_order_value
FROM orders
GROUP BY status
ORDER BY orders DESC;


-- Average Shipping Days by Region
SELECT
    c.region,
    ROUND(AVG(o.shipping_days), 1)  AS avg_shipping_days,
    MIN(o.shipping_days)            AS min_days,
    MAX(o.shipping_days)            AS max_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'Delivered'
  AND o.shipping_days IS NOT NULL
GROUP BY c.region
ORDER BY avg_shipping_days;
