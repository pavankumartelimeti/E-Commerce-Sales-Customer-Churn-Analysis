# Power BI Dashboard Setup Guide
## E-Commerce Sales & Churn Analysis

---

## Step 1 — Connect Data Sources

Open Power BI Desktop → **Get Data**

### Option A: SQLite Database
1. Get Data → **ODBC** → DSN: point to `python/ecommerce.db`
2. Import tables: `customers`, `products`, `orders`, `order_items`

### Option B: CSV Files (easier)
1. Get Data → **Text/CSV**
2. Load all 4 CSVs from the `data/` folder
3. Load `churn_predictions.csv` from `python/outputs/`

---

## Step 2 — Data Model (Star Schema)

Set relationships in **Model View**:

```
orders ──────── customers    (orders.customer_id → customers.customer_id)
orders ──────── order_items  (orders.order_id    → order_items.order_id)
order_items ─── products     (order_items.product_id → products.product_id)
orders ──────── churn_predictions (orders.customer_id → churn_predictions.customer_id)
```

---

## Step 3 — DAX Measures

Paste these into a dedicated **Measures Table**:

```dax
-- Core KPIs
Total Revenue = CALCULATE(SUM(orders[total_amount]), orders[status] = "Delivered")

Total Orders = CALCULATE(DISTINCTCOUNT(orders[order_id]), orders[status] = "Delivered")

Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Unique Customers = DISTINCTCOUNT(orders[customer_id])

-- Churn
Churned Customers =
    CALCULATE(
        DISTINCTCOUNT(customers[customer_id]),
        FILTER(
            ALL(orders),
            DATEDIFF(MAX(orders[order_date]), DATE(2024,12,31), DAY) > 180
        )
    )

Churn Rate % =
    DIVIDE([Churned Customers], [Unique Customers]) * 100

-- Profit
Gross Profit =
    SUMX(
        order_items,
        order_items[line_total] - (order_items[quantity] * RELATED(products[cost_price]))
    )

Profit Margin % = DIVIDE([Gross Profit], [Total Revenue]) * 100

-- MoM Growth
Revenue MoM Growth % =
    VAR CurrentMonth = [Total Revenue]
    VAR PreviousMonth =
        CALCULATE([Total Revenue], DATEADD('orders'[order_date], -1, MONTH))
    RETURN DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth) * 100

-- Return Rate
Return Rate % =
    DIVIDE(
        CALCULATE(COUNTROWS(orders), orders[status] = "Returned"),
        COUNTROWS(orders)
    ) * 100
```

---

## Step 4 — Dashboard Pages

### 📌 Page 1: Executive Summary
| Visual | Fields |
|--------|--------|
| Card (4x) | Total Revenue, Orders, AOV, Churn Rate % |
| Line Chart | order_date (month) vs Total Revenue |
| Bar Chart | region vs Total Revenue |
| Donut | order_status count |
| Slicer | Year, Region, Category |

### 📌 Page 2: Customer Intelligence
| Visual | Fields |
|--------|--------|
| Scatter Plot | recency vs monetary (size = frequency) |
| Bar Chart | loyalty_tier vs Total Revenue |
| Map | region vs Churn Rate % |
| Table | customer_id, CLV, segment, churn_probability |
| Slicer | predicted_segment (High/Medium/Low Risk) |

### 📌 Page 3: Product & Category
| Visual | Fields |
|--------|--------|
| Treemap | category → product_name (Revenue) |
| Bar Chart | Top 10 products by revenue |
| Matrix | category × month (Revenue heatmap) |
| KPI Card | Profit Margin % |
| Gauge | Avg Discount % |

### 📌 Page 4: Operations
| Visual | Fields |
|--------|--------|
| Clustered Bar | payment_method vs Orders |
| Line + Bar | shipping_days trend |
| Table | Low Stock products (stock < 50) |
| Funnel | Order status funnel |

---

## Step 5 — Formatting Tips

- **Theme**: Import a custom theme JSON or use "Executive" built-in
- **Brand Colors**: `#0D47A1` (primary), `#E53935` (alert), `#43A047` (positive)
- **Bookmarks**: Add "Churned Customers View" and "Top Region View" bookmarks
- **Drill-through**: Set up drill-through from Category page → Product detail
- **Tooltips**: Custom tooltip page showing customer purchase history

---

## Suggested Insights to Highlight on Resume

1. **"Identified 30% customer churn rate concentrated in the North region"**
2. **"Built Random Forest model achieving 1.00 AUC to predict at-risk customers"**
3. **"Discovered Electronics drives 28% of revenue but has highest return rate"**
4. **"Designed Power BI dashboard with 4 pages and 12+ DAX measures for exec reporting"**
5. **"Segmented 2,000 customers using RFM analysis into 6 behavioral groups"**
