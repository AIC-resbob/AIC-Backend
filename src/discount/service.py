import os
import math
from datetime import datetime, date
import joblib
import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional

# Load model and metadata once at startup
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "discount_demand_response_model.joblib")
META_PATH = os.path.join(MODELS_DIR, "discount_engine_meta.joblib")

model = joblib.load(MODEL_PATH)
meta = joblib.load(META_PATH)
DATA_START = pd.to_datetime(meta.get("data_start", "2025-08-18"))

def is_indonesian_payday(eval_date: date) -> int:
    """Payday window: 25th of month to the 1st of the next month."""
    return 1 if (eval_date.day >= 25 or eval_date.day == 1) else 0

def is_ramadan_season(eval_date: date) -> int:
    """Approximate flag for Indonesian seasonal spikes."""
    # Ramadan 2026 approx: mid-Feb to late March
    if eval_date.year == 2026 and (eval_date.month == 2 or eval_date.month == 3):
        return 1
    if eval_date.year == 2025 and (eval_date.month == 3 or eval_date.month == 4):
        return 1
    return 0

def compute_calendar_features(eval_date: date):
    dt = pd.to_datetime(eval_date)
    trend = (dt - DATA_START).days
    dow = eval_date.weekday()
    dow_sin = math.sin(2 * math.pi * dow / 7.0)
    dow_cos = math.cos(2 * math.pi * dow / 7.0)
    is_gajian = is_indonesian_payday(eval_date)
    is_ramadan = is_ramadan_season(eval_date)

    return {
        "trend": trend,
        "dow_sin": dow_sin,
        "dow_cos": dow_cos,
        "is_periode_gajian": is_gajian,
        "is_ramadan": is_ramadan,
    }

def recommend_optimal_discount(
    kategori: str,
    selling_price: float,
    cogs: float,
    current_stock: int,
    days_to_expiry: int,
    eval_date: Optional[date] = None,
    target_days: int = 7,
    service_level: float = 0.80
) -> dict:
    if eval_date is None:
        eval_date = date.today()

    cal = compute_calendar_features(eval_date)


    max_safe_discount = max(0.0, (selling_price - cogs) / selling_price)


    candidate_discounts = [i * 0.05 for i in range(0, 11)]

    valid_candidates = [d for d in candidate_discounts if d <= max_safe_discount]
    if not valid_candidates:
        valid_candidates = [0.0]

    rows = []
    for d in valid_candidates:
        discounted_price = selling_price * (1.0 - d)

        price_ratio = discounted_price / selling_price
        log_price_ratio = math.log(max(price_ratio, 1e-4))

        rows.append({
            "log_price_ratio": log_price_ratio,
            "trend": cal["trend"],
            "dow_sin": cal["dow_sin"],
            "dow_cos": cal["dow_cos"],
            "is_periode_gajian": cal["is_periode_gajian"],
            "is_ramadan": cal["is_ramadan"],
            "days_to_expiry": days_to_expiry,
            "stock_akhir": current_stock,
            "kategori": str(kategori),
            "discount_pct": d,
            "discounted_price": discounted_price,
            "margin_per_unit": discounted_price - cogs
        })

    df = pd.DataFrame(rows)


    df["kategori"] = df["kategori"].astype("category")

    features = [
        "log_price_ratio", "trend", "dow_sin", "dow_cos",
        "is_periode_gajian", "is_ramadan", "days_to_expiry",
        "stock_akhir", "kategori"
    ]

    preds = model.predict(df[features])
    df["pred_daily_demand"] = np.clip(preds, a_min=0, a_max=None)

    # For each candidate discount, estimate the probability that demand over `target_days`
    # actually clears `current_stock` (Poisson demand, matching the notebook's discount
    # engine) - a pure expected-profit argmax has no penalty for leftover unsold stock, so it
    # never recommends a discount unless the model's own elasticity happens to make the
    # discounted margin outweigh the extra units on its own. That defeats the point of an
    # "overstock/clear it out" recommendation, since most of the stock can go unsold with no
    # consequence to the score. Picking the smallest discount that hits a target clearance
    # probability (falling back to whichever gets closest) actually optimizes for clearance.
    evaluations = []
    candidates = []

    for idx, row in df.iterrows():
        mean_total_demand = float(row["pred_daily_demand"] * target_days)
        est_sales_period = min(float(current_stock), mean_total_demand)
        est_profit = est_sales_period * row["margin_per_unit"]
        prob_clear = float(stats.poisson.sf(current_stock - 1, max(mean_total_demand, 1e-6)))

        cand_data = {
            "discount_pct": round(row["discount_pct"] * 100, 1),
            "discounted_price": round(row["discounted_price"], 2),
            "margin_per_unit": round(row["margin_per_unit"], 2),
            "predicted_daily_demand": round(float(row["pred_daily_demand"]), 2),
            "expected_units_sold": round(est_sales_period, 2),
            "expected_profit": round(est_profit, 2)
        }
        evaluations.append(cand_data)
        candidates.append({**cand_data, "prob_clear": prob_clear})

    feasible = [c for c in candidates if c["prob_clear"] >= service_level]
    if feasible:
        best_candidate = min(feasible, key=lambda c: c["discount_pct"])
        status_msg = "OPTIMAL_PROFIT"
    else:
        best_candidate = max(candidates, key=lambda c: c["prob_clear"])
        status_msg = "CLEARANCE_URGENT"

    return {
        "recommended_discount_pct": best_candidate["discount_pct"],
        "recommended_price": best_candidate["discounted_price"],
        "max_safe_discount_pct": round(max_safe_discount * 100, 1),
        "estimated_units_sold": best_candidate["expected_units_sold"],
        "estimated_profit": best_candidate["expected_profit"],
        "status": status_msg,
        "evaluation_candidates": evaluations
    }
