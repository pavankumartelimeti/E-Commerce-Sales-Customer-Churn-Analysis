# 🛒 E-Commerce Sales & Churn Analysis
**Resume Project | Python · SQL · Power BI**

---

## Problem Statement
An e-commerce company faces declining repeat purchases and poor inventory decisions.
This project analyzes 3 years of transaction data to:
- Identify customer churn patterns and predict at-risk customers
- Uncover top-performing products and categories
- Surface regional and operational inefficiencies

---

## Tech Stack
| Tool | Usage |
|------|-------|
| **Python** | Data generation, EDA, visualizations, ML churn model |
| **SQL (SQLite)** | Schema design, RFM segmentation, KPI queries |
| **Power BI** | Interactive executive dashboard |
| **scikit-learn** | Random Forest churn classifier |
| **pandas / matplotlib** | Data wrangling & charts |

---

## Dataset
| Table | Rows | Description |
|-------|------|-------------|
| customers | 2,000 | Demographics, region, loyalty tier |
| products | 150 | Category, pricing, stock |
| orders | 15,000 | Transactions, status, payment |
| order_items | 45,000 | Line-level product details |

---

## How to Run

```bash
# 1. Install dependencies
pip install -r python/requirements.txt

# 2. Generate dataset
python data/generate_data.py

# 3. Run EDA + create SQLite DB
python python/eda.py

# 4. Run churn prediction model
python python/churn_model.py

# 5. Open Power BI and follow powerbi/dashboard_guide.md
```

---

## Key Findings
- **49% churn rate** — customers with no purchase in 180+ days
- **Recency** is the strongest churn predictor (most important feature)
- **Electronics & Clothing** drive 45%+ of total revenue
- **North region** has the highest churn rate
- Random Forest model achieves **AUC: 1.00** on test set

---

## Outputs
- `python/outputs/` — 9 analysis charts (PNG)
- `python/outputs/churn_predictions.csv` — churn scores for all customers
- `python/ecommerce.db` — SQLite database for Power BI connection
- `sql/analysis_queries.sql` — 12 production-ready SQL queries

---

## Resume Bullet Points (Copy-Paste Ready)
- Built end-to-end e-commerce analytics pipeline using Python, SQL, and Power BI on 60K+ row dataset
- Designed RFM segmentation model to classify 2,000 customers into 6 behavioral cohorts
- Trained Random Forest churn classifier (AUC 1.00) identifying high-risk customers for retention campaigns
- Wrote 12 optimized SQL queries covering CLV, churn rate, category mix, and inventory analysis
- Delivered 4-page Power BI executive dashboard with 12+ DAX measures and drill-through capabilities
