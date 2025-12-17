# NextGen/app/ai_engine.py
# NGIM AI ENGINE — Monthly Forecast + Inventory + Month-based Combos (product names only)

import os
import math
import warnings
from datetime import timedelta
import pandas as pd
import numpy as np

# ML (XGBoost)
from xgboost import XGBRegressor

# FP-growth
from mlxtend.frequent_patterns import fpgrowth, association_rules

warnings.filterwarnings("ignore")

# ----------------------------
# PATHS (adjust if needed)
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # NextGen/app
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")     # NextGen/data

SALES_PATH = os.path.join(DATA_DIR, "sales_100_indian_3yrs.csv")
PRODUCTS_PATH = os.path.join(DATA_DIR, "products_100_indian_3yrs.csv")

# ----------------------------
# FP-GROWTH USER PARAMS (editable)
# ----------------------------
MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.10
MAX_COMBOS = 10
SUGGESTED_DISCOUNT = "10%"

FESTIVAL_NAMES_BY_MONTH = {
    1: ("Sankranti", "New Year Specials"),
    2: ("Ugadi", "Valentine's Treat"),
    3: ("Holi", "Holi Offer"),
    4: ("Ram Navami", "Spring Sale"),
    5: ("Akshaya Tritiya", "Summer Essentials"),
    6: ("Monsoon Treat", "Monsoon Specials"),
    7: ("Guru Purnima", "Midyear Treat"),
    8: ("Independence Combo", "Raksha Bandhan Special"),
    9: ("Ganesh Offer", "Festive Picks"),
    10: ("Diwali Dhamaka", "Dussehra Delight"),
    11: ("Diwali", "Wedding Season Pack"),
    12: ("Christmas Combo", "Year End Deals"),
}

# ----------------------------
# 1. Load CSVs
# ----------------------------
if not os.path.exists(SALES_PATH) or not os.path.exists(PRODUCTS_PATH):
    raise FileNotFoundError(f"Expected CSVs at:\n {SALES_PATH}\n {PRODUCTS_PATH}")

sales = pd.read_csv(SALES_PATH)
products = pd.read_csv(PRODUCTS_PATH)

# Normalize invoice_date
sales["invoice_date"] = pd.to_datetime(sales["invoice_date"].astype(str).str.strip(), errors="coerce")
sales = sales.dropna(subset=["invoice_date"]).copy()
sales["invoice_month"] = sales["invoice_date"].dt.to_period("M").dt.to_timestamp()

# Ensure numeric columns
if "quantity" not in sales.columns:
    sales["quantity"] = 1
if "unit_price" not in sales.columns:
    sales["unit_price"] = 0.0

if "category" not in products.columns:
    products["category"] = "Unknown"
if "base_price" not in products.columns:
    products["base_price"] = 0.0

products["category_id"] = products["category"].astype("category").cat.codes

# ----------------------------
# 2. Monthly aggregation + features
# ----------------------------
monthly = (
    sales
    .groupby(["invoice_month", "product_id"], as_index=False)
    .agg(monthly_qty=("quantity", "sum"),
         monthly_revenue=("unit_price", "sum"))
)
monthly = monthly.merge(products, on="product_id", how="left")
monthly = monthly.sort_values(["product_id", "invoice_month"]).reset_index(drop=True)

monthly["lag_1_qty"] = monthly.groupby("product_id")["monthly_qty"].shift(1)
monthly["rolling_3_qty"] = (
    monthly.groupby("product_id")["monthly_qty"]
    .rolling(3, min_periods=1).mean()
    .reset_index(level=0, drop=True)
)
monthly["year"] = monthly["invoice_month"].dt.year
monthly["month"] = monthly["invoice_month"].dt.month
monthly["category_id"] = monthly["category"].astype("category").cat.codes
monthly["target_qty"] = monthly["monthly_qty"]

model_data = monthly.dropna(subset=["lag_1_qty"]).copy()

feature_cols = [
    "product_id",
    "base_price",
    "category_id",
    "lag_1_qty",
    "rolling_3_qty",
    "year",
    "month",
]

if model_data.shape[0] == 0:
    model_data = pd.DataFrame(columns=feature_cols + ["target_qty"])

# ----------------------------
# 3. Train XGBoost (or stub)
# ----------------------------
def _train_model():
    if model_data.shape[0] >= 10:
        X = model_data[feature_cols].astype(float)
        y = model_data["target_qty"].astype(float)
        m = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        )
        m.fit(X, y)
        return m
    else:
        class StubModel:
            def predict(self, X):
                out = []
                for _, row in X.iterrows():
                    pid = int(row["product_id"])
                    hist = monthly[monthly["product_id"] == pid]
                    out.append(hist["monthly_qty"].mean() if hist.shape[0] > 0 else 0.0)
                return np.array(out)
        return StubModel()

model = _train_model()

# ----------------------------
# 4. FP-Growth combos (product NAMES, month-aware)
#    - compute_combos_for_month(forecast_month_str)
# ----------------------------
def _parse_month_str(month_str):
    """Accept 'YYYY-MM' or 'YYYY-MM-DD' and return (year, month) ints."""
    try:
        ts = pd.to_datetime(month_str)
        return ts.year, ts.month
    except Exception:
        raise ValueError("Invalid month string. Expect 'YYYY-MM' or 'YYYY-MM-DD'.")

def compute_combos_for_month_str(forecast_month_str=None,
                                 min_support=MIN_SUPPORT,
                                 min_conf=MIN_CONFIDENCE,
                                 max_combos=MAX_COMBOS):
    """
    Return list of combos (each: {'products': [nameA, nameB]})
    If forecast_month_str provided: attempts to compute combos using previous-year same month
    (i.e., use (year-1, month) data). If not enough data, falls back to recent 3 months.
    Only product NAMES are returned (no lift field).
    """
    df_sales = sales.copy()
    target_sf = pd.DataFrame()

    # If user passed a month string, parse and use previous year same month
    if forecast_month_str:
        try:
            year, month = _parse_month_str(forecast_month_str)
            prev_year = int(year) - 1
            sf = df_sales[(df_sales["invoice_date"].dt.year == prev_year) & (df_sales["invoice_date"].dt.month == month)].copy()
            if sf.shape[0] > 0:
                target_sf = sf
        except Exception:
            target_sf = pd.DataFrame()

    # If previous-year-month not available, use recent 3 months
    if target_sf.shape[0] == 0:
        last_date = df_sales["invoice_date"].max()
        start_for_combos = last_date - pd.DateOffset(months=3)
        target_sf = df_sales[df_sales["invoice_date"] >= start_for_combos].copy()

    if target_sf.shape[0] == 0:
        return []

    # Convert basket: invoice_id x product_id
    basket = (
        target_sf
        .groupby(["invoice_id", "product_id"])["quantity"]
        .sum()
        .unstack(fill_value=0)
    )
    if basket.shape[1] == 0:
        return []

    basket_binary = (basket > 0).astype(int)

    try:
        freq = fpgrowth(basket_binary, min_support=min_support, use_colnames=True, max_len=2)
    except Exception:
        return []

    if freq.empty:
        return []

    rules = association_rules(freq, metric="confidence", min_threshold=min_conf)
    if rules.empty:
        return []

    # Keep only pair rules (one antecedent + one consequent)
    rules["ant_len"] = rules["antecedents"].apply(len)
    rules["cons_len"] = rules["consequents"].apply(len)
    pair_rules = rules[(rules["ant_len"] + rules["cons_len"]) == 2].copy()
    if pair_rules.shape[0] == 0:
        return []

    # Remove symmetric duplicates: pick best per unordered pair
    def pair_key(row):
        items = sorted(list(row["antecedents"] | row["consequents"]))
        return tuple(items)

    pair_rules["pair"] = pair_rules.apply(pair_key, axis=1)
    pair_best = pair_rules.sort_values(["pair", "lift", "confidence"], ascending=[True, False, False]).drop_duplicates("pair", keep="first").copy()

    # Build candidate pairs and greedy-select top unique pairs
    pair_best["product_A_id"] = pair_best["pair"].apply(lambda t: list(t)[0])
    pair_best["product_B_id"] = pair_best["pair"].apply(lambda t: list(t)[1])
    pair_best = pair_best[["product_A_id", "product_B_id", "support", "confidence", "lift"]]

    # Convert ids -> names using products DF
    id_to_name = products.set_index("product_id")["product_name"].to_dict()
    pair_best["product_A_name"] = pair_best["product_A_id"].apply(lambda x: id_to_name.get(x, str(x)))
    pair_best["product_B_name"] = pair_best["product_B_id"].apply(lambda x: id_to_name.get(x, str(x)))

    # sort and greedy select (unique products only)
    candidates = pair_best.sort_values(["lift", "confidence", "support"], ascending=[False, False, False]).reset_index(drop=True)
    selected = []
    used = set()
    for _, r in candidates.iterrows():
        a_name = r["product_A_name"]; b_name = r["product_B_name"]
        if a_name in used or b_name in used:
            continue
        selected.append((a_name, b_name))
        used.add(a_name); used.add(b_name)
        if len(selected) >= max_combos:
            break

    # return list of dicts with product names only
    combos = [{"products": [a, b]} for (a, b) in selected]
    return combos

# ----------------------------
# 5. Inventory helper
# ----------------------------
def compute_inventory(forecast_qty, stock):
    forecast_qty = float(forecast_qty or 0.0)
    stock = float(stock or 0.0)
    avg_daily = round(forecast_qty / 30.0, 2)
    days_supply = round(stock / (avg_daily if avg_daily > 0 else 1), 1)
    target_stock = math.ceil(forecast_qty * 1.1)
    suggested_order = int(max(0, target_stock - stock))
    return {"avg_daily": avg_daily, "days_of_supply": days_supply, "suggested_order": suggested_order}

# ----------------------------
# 6. Forecast single product / month
# ----------------------------
def forecast_product_month(pid, forecast_month):
    pid = int(pid)
    try:
        ts = pd.to_datetime(forecast_month + "-01")
    except Exception:
        ts = pd.to_datetime(forecast_month)
    hist = monthly[(monthly["product_id"] == pid) & (monthly["invoice_month"] < ts)].sort_values("invoice_month")
    if hist.shape[0] == 0:
        return 0.0
    last = hist.iloc[-1]
    last3 = hist.tail(3)
    prod_meta = products[products["product_id"] == pid].iloc[0]
    X_input = pd.DataFrame([{
        "product_id": pid,
        "base_price": prod_meta.get("base_price", 0.0),
        "category_id": prod_meta.get("category_id", 0),
        "lag_1_qty": last["monthly_qty"],
        "rolling_3_qty": last3["monthly_qty"].mean() if last3.shape[0] > 0 else last["monthly_qty"],
        "year": ts.year,
        "month": ts.month
    }])
    X_input = X_input[feature_cols].astype(float)
    try:
        pred = float(model.predict(X_input)[0])
    except Exception:
        pred = float(hist["monthly_qty"].mean())
    return max(0.0, pred)

# ----------------------------
# 7. Seasonal analysis
# ----------------------------
def seasonal_analysis(pid):
    pid = int(pid)
    df = monthly[monthly["product_id"] == pid]
    if df.empty:
        return {"peak_month": "—", "low_month": "—"}
    month_sum = df.groupby("month")["monthly_qty"].sum()
    peak = int(month_sum.idxmax())
    low = int(month_sum.idxmin())
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return {"peak_month": months[peak-1], "low_month": months[low-1]}

# ----------------------------
# 8. get_recommendation (UI entry)
# ----------------------------
def get_recommendation(pid, forecast_month, stock):
    pid = int(pid)
    # numeric stock
    try:
        stock = float(stock)
    except:
        stock = 0.0

    forecast_qty = forecast_product_month(pid, forecast_month)
    if forecast_qty == 0:
        hist = monthly[monthly["product_id"] == pid]
        forecast_qty = float(hist["monthly_qty"].mean()) if hist.shape[0] > 0 else 0.0

    daily_val = int(round(forecast_qty / 30.0)) if forecast_qty > 0 else 0
    forecast_list = [daily_val for _ in range(30)]

    base = pd.Timestamp.now().normalize()
    daily_breakdown = []
    for i, v in enumerate(forecast_list):
        date = (base + timedelta(days=i+1)).strftime("%b %d, %Y")
        prev = forecast_list[i-1] if i > 0 else v
        trend = "up" if v > prev else "down" if v < prev else "flat"
        daily_breakdown.append((date, int(v), trend))

    product = products[products["product_id"] == pid].iloc[0]

    # compute bundles specific to the selected month (previous year same month if available)
    try:
        bundles = compute_combos_for_month_str(forecast_month, min_support=MIN_SUPPORT, min_conf=MIN_CONFIDENCE, max_combos=MAX_COMBOS)
        if not bundles:
            # ensure at least one friendly message if empty
            bundles = [{"products": ["No Data"]}]
    except Exception:
        bundles = [{"products": ["No Data"]}]

    return {
        "product": product,
        "forecast_list": forecast_list,
        "forecast_total": int(sum(forecast_list)),
        "daily_breakdown_triple": daily_breakdown,
        "daily_avg": int(np.mean(forecast_list)) if len(forecast_list) else 0,
        "daily_min": int(np.min(forecast_list)) if len(forecast_list) else 0,
        "daily_max": int(np.max(forecast_list)) if len(forecast_list) else 0,
        "inventory": compute_inventory(forecast_qty, stock),
        "season": seasonal_analysis(pid),
        "bundles": bundles,
        "days": 30,
        "stock": stock,
        "forecast_month": forecast_month
    }

# ----------------------------
# 9. Top-10 forecast report (for dashboard)
# ----------------------------
def get_top10_forecast(forecast_month):
    rows = []
    for pid in products["product_id"].unique():
        qty = forecast_product_month(pid, forecast_month)
        prod = products[products["product_id"] == pid].iloc[0]

        rows.append({
            "product_id": int(pid),
            "product_name": prod.get("product_name", f"P{pid}"),
            "forecast_qty": int(round(qty))
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return []

    df = df.sort_values("forecast_qty", ascending=False).head(10)
    return df.to_dict(orient="records")


# ----------------------------
# 10. Helpers for Flask UI
# ----------------------------
def get_products():
    return products.copy()

def refresh_combo_cache(min_support=MIN_SUPPORT, max_results=MAX_COMBOS):
    """
    Refreshes the precomputed combo_cache (recent 3 months).
    This can be called from an admin endpoint if desired.
    """
    global combo_cache
    try:
        combos = compute_combos_for_month_str(None, min_support=min_support, min_conf=MIN_CONFIDENCE, max_combos=max_results)
        combo_cache = combos
    except Exception:
        combo_cache = []
    return combo_cache

# ----------------------------
# Optional pre-cache (recent 3 months) — used only when needed
# ----------------------------
try:
    combo_cache = compute_combos_for_month_str(None, min_support=MIN_SUPPORT, min_conf=MIN_CONFIDENCE, max_combos=MAX_COMBOS)
except Exception:
    combo_cache = []

print(f"ai_engine loaded — products={len(products)}, sales_rows={len(sales)}, combos_cached={len(combo_cache)}")
