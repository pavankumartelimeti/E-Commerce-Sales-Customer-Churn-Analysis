"""
E-Commerce Customer Churn Prediction
Model: Random Forest Classifier
Features: RFM + demographics
Run: python churn_model.py
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve, ConfusionMatrixDisplay)
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, "ecommerce.db")
OUT  = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)


# ── Feature Engineering ───────────────────────────────────────
def build_features(conn):
    rfm = pd.read_sql("""
        SELECT
            o.customer_id,
            JULIANDAY('2024-12-31') - JULIANDAY(MAX(o.order_date)) AS recency,
            COUNT(DISTINCT o.order_id)                              AS frequency,
            ROUND(SUM(o.total_amount), 2)                          AS monetary,
            ROUND(AVG(o.total_amount), 2)                          AS avg_order_value,
            MIN(o.shipping_days)                                    AS min_shipping,
            ROUND(AVG(o.shipping_days), 1)                         AS avg_shipping,
            SUM(CASE WHEN o.status='Returned'  THEN 1 ELSE 0 END)  AS returns,
            SUM(CASE WHEN o.status='Cancelled' THEN 1 ELSE 0 END)  AS cancellations,
            ROUND(AVG(oi.discount_pct), 3)                         AS avg_discount
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.customer_id
    """, conn)

    customers = pd.read_sql("SELECT * FROM customers", conn)
    df = rfm.merge(customers, on="customer_id")

    # Label: churned = no purchase in last 180 days
    df["churned"] = (df["recency"] > 180).astype(int)

    # Encode categoricals
    for col in ["gender", "region", "loyalty_tier"]:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    df["registration_date"] = pd.to_datetime(df["registration_date"])
    df["tenure_days"] = (pd.Timestamp("2024-12-31") - df["registration_date"]).dt.days

    features = ["recency", "frequency", "monetary", "avg_order_value",
                "avg_shipping", "returns", "cancellations", "avg_discount",
                "age", "gender", "region", "loyalty_tier", "tenure_days"]

    df = df.dropna(subset=features)
    return df[features + ["churned", "customer_id"]]


# ── Train Model ───────────────────────────────────────────────
def train_and_evaluate(df):
    X = df.drop(columns=["churned", "customer_id"])
    y = df["churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=5,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n" + "="*50)
    print("   🤖 CHURN MODEL RESULTS")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=["Active", "Churned"]))
    print(f"   ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    print(f"   5-Fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print("="*50)

    return model, X_test, y_test, y_pred, y_proba, X.columns.tolist()


# ── Plots ─────────────────────────────────────────────────────
def plot_feature_importance(model, feature_names):
    imp = pd.Series(model.feature_importances_, index=feature_names).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#E53935" if i >= len(imp) - 3 else "#1976D2" for i in range(len(imp))]
    ax.barh(imp.index, imp.values, color=colors)
    ax.set_title("Feature Importance — Churn Prediction Model", fontsize=13, fontweight="bold")
    ax.set_xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(f"{OUT}/07_feature_importance.png"); plt.close()
    print("📊 Feature importance saved.")


def plot_roc_curve(y_test, y_proba):
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#1976D2", lw=2, label=f"AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.fill_between(fpr, tpr, alpha=0.1, color="#1976D2")
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — Customer Churn Model", fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(f"{OUT}/08_roc_curve.png"); plt.close()
    print("📊 ROC curve saved.")


def plot_confusion_matrix(y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(cm, display_labels=["Active", "Churned"])
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion Matrix", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUT}/09_confusion_matrix.png"); plt.close()
    print("📊 Confusion matrix saved.")


def export_churn_predictions(model, df, conn):
    X = df.drop(columns=["churned", "customer_id"])
    df = df.copy()
    df["churn_probability"] = model.predict_proba(X)[:, 1].round(4)
    df["predicted_segment"] = df["churn_probability"].apply(
        lambda p: "High Risk" if p > 0.7 else ("Medium Risk" if p > 0.4 else "Low Risk")
    )
    out_path = f"{OUT}/churn_predictions.csv"
    df[["customer_id", "churn_probability", "predicted_segment"]].to_csv(out_path, index=False)
    print(f"💾 Churn predictions exported: {out_path}")

    seg_counts = df["predicted_segment"].value_counts()
    print("\n   Segment Breakdown:")
    for seg, cnt in seg_counts.items():
        print(f"   {seg:<15} {cnt:>5} customers")


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(DB):
        print("❌ Run eda.py first to create the SQLite database.")
        exit(1)

    conn = sqlite3.connect(DB)
    print("🔧 Building feature matrix...")
    df = build_features(conn)
    print(f"   Dataset: {len(df):,} customers | Churn rate: {df['churned'].mean()*100:.1f}%")

    model, X_test, y_test, y_pred, y_proba, feat_names = train_and_evaluate(df)
    plot_feature_importance(model, feat_names)
    plot_roc_curve(y_test, y_proba)
    plot_confusion_matrix(y_test, y_pred)
    export_churn_predictions(model, df, conn)

    conn.close()
    print("\n✅ Churn model complete. All outputs in python/outputs/\n")
