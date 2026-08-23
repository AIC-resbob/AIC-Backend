import os
import math
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import joblib
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from db_models import Product, Inventory, Transaction

# Load model and metadata
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "restock_predictor_model.joblib")
META_PATH = os.path.join(MODELS_DIR, "restock_predictor_meta.joblib")

model = joblib.load(MODEL_PATH)
meta = joblib.load(META_PATH)

DEFAULT_RESIDUAL_STD = float(meta.get("residual_std", 20.3676))
DEFAULT_SERVICE_Z = float(meta.get("service_level_z", 1.28))
DATA_START = pd.to_datetime("2025-08-18")

def is_indonesian_payday(eval_date: date) -> int:
    return 1 if (eval_date.day >= 25 or eval_date.day == 1) else 0

def is_ramadan_season(eval_date: date) -> int:
    if eval_date.year == 2026 and (eval_date.month in [2, 3]):
        return 1
    if eval_date.year == 2025 and (eval_date.month in [3, 4]):
        return 1
    return 0

def calculate_window_fractions(eval_date: date, window_days: int = 7) -> Tuple[float, float]:
    gajian_count = 0
    ramadan_count = 0
    for i in range(window_days):
        d = eval_date + timedelta(days=i)
        gajian_count += is_indonesian_payday(d)
        ramadan_count += is_ramadan_season(d)
    return (gajian_count / window_days, ramadan_count / window_days)

def compute_historical_time_series_features(db: Session, product_id: int, eval_date: date) -> dict:
    """Aggregates transaction history from SQLite for time-series features."""
    lookback_start = eval_date - timedelta(days=35)
    
    # Query transactions within lookback window
    txs = db.query(Transaction).filter(
        Transaction.product_id == product_id,
        Transaction.transaction_date >= datetime.combine(lookback_start, datetime.min.time()),
        Transaction.transaction_date <= datetime.combine(eval_date, datetime.max.time())
    ).all()

    # Aggregate daily sales
    daily_sales = {}
    for tx in txs:
        t_date = tx.transaction_date.date()
        daily_sales[t_date] = daily_sales.get(t_date, 0) + tx.quantity_sold

    # Construct daily series for the last 30 days
    series = []
    for i in range(30, -1, -1):
        d = eval_date - timedelta(days=i)
        series.append(daily_sales.get(d, 0.0))

    series = pd.Series(series)

    # Compute lags (relative to today)
    demand_today = float(series.iloc[-1])
    lag_1 = float(series.iloc[-2]) if len(series) >= 2 else demand_today
    lag_7 = float(series.iloc[-8]) if len(series) >= 8 else demand_today
    lag_14 = float(series.iloc[-15]) if len(series) >= 15 else demand_today
    lag_28 = float(series.iloc[-29]) if len(series) >= 29 else demand_today

    # Rolling statistics
    roll_7 = series.iloc[-7:]
    roll_14 = series.iloc[-14:]
    roll_28 = series.iloc[-28:]

    roll_mean_7 = float(roll_7.mean())
    roll_std_7 = float(roll_7.std(ddof=0)) if len(roll_7) > 1 else 0.0
    roll_mean_14 = float(roll_14.mean())
    roll_mean_28 = float(roll_28.mean())

    return {
        "demand_today": demand_today,
        "lag_1": lag_1,
        "lag_7": lag_7,
        "lag_14": lag_14,
        "lag_28": lag_28,
        "roll_mean_7": roll_mean_7,
        "roll_std_7": roll_std_7,
        "roll_mean_14": roll_mean_14,
        "roll_mean_28": roll_mean_28,
    }

def forecast_restock(
    db: Session,
    product: Product,
    inv: Inventory,
    eval_date: Optional[date] = None,
    target_days: int = 7,
    service_level_z: Optional[float] = None
) -> dict:
    if eval_date is None:
        eval_date = date.today()

    z = service_level_z if service_level_z is not None else DEFAULT_SERVICE_Z

    # 1. Historical time series lags
    ts_features = compute_historical_time_series_features(db, product.id, eval_date)

    # 2. Calendar & Cyclical features
    trend = (pd.to_datetime(eval_date) - DATA_START).days
    dow = eval_date.weekday()
    dow_sin = math.sin(2 * math.pi * dow / 7.0)
    dow_cos = math.cos(2 * math.pi * dow / 7.0)
    is_gajian = is_indonesian_payday(eval_date)
    is_ramadan = is_ramadan_season(eval_date)
    frac_gajian, frac_ramadan = calculate_window_fractions(eval_date, window_days=7)

    # Price ratio (default to 1.0 if not on promo)
    price_ratio = 1.0

    # Build single-row DataFrame for model
    feature_row = {
        "lag_1": float(ts_features["lag_1"]),
        "lag_7": float(ts_features["lag_7"]),
        "lag_14": float(ts_features["lag_14"]),
        "lag_28": float(ts_features["lag_28"]),
        "demand_today": float(ts_features["demand_today"]),
        "roll_mean_7": float(ts_features["roll_mean_7"]),
        "roll_std_7": float(ts_features["roll_std_7"]),
        "roll_mean_14": float(ts_features["roll_mean_14"]),
        "roll_mean_28": float(ts_features["roll_mean_28"]),
        "stock_akhir": float(inv.current_stock),
        "price_ratio": float(price_ratio),
        "trend": float(trend),
        "dow_sin": float(dow_sin),
        "dow_cos": float(dow_cos),
        "is_periode_gajian": int(is_gajian),
        "is_ramadan": int(is_ramadan),
        "is_periode_gajian_frac_7d": float(frac_gajian),
        "is_ramadan_frac_7d": float(frac_ramadan),
        "kategori": str(product.category),
        "product_id": str(product.id), 
    }

    df = pd.DataFrame([feature_row])
    expected_features = [
        "lag_1", "lag_7", "lag_14", "lag_28", "demand_today",
        "roll_mean_7", "roll_std_7", "roll_mean_14", "roll_mean_28",
        "stock_akhir", "price_ratio", "trend", "dow_sin", "dow_cos",
        "is_periode_gajian", "is_ramadan", "is_periode_gajian_frac_7d",
        "is_ramadan_frac_7d", "kategori", "product_id"
    ]

    predicted_7d_raw = float(model.predict(df[expected_features])[0])
    predicted_7d = max(0.0, predicted_7d_raw)

    # Scale daily rate to target days
    daily_demand = predicted_7d / 7.0
    predicted_target_demand = daily_demand * target_days

    # Compute safety stock and final restock recommendation based on target days
    safety_stock = z * DEFAULT_RESIDUAL_STD * math.sqrt(target_days / 7.0)
    gross_requirement = predicted_target_demand + safety_stock
    needed_qty = gross_requirement - inv.current_stock
    recommended_restock = max(0, math.ceil(needed_qty))

    # Urgency categorization
    if inv.current_stock <= (predicted_7d * 0.3):
        urgency = "CRITICAL_STOCKOUT_RISK"
    elif needed_qty > 0:
        urgency = "RESTOCK_RECOMMENDED"
    else:
        urgency = "STOCK_SUFFICIENT"

    return {
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category,
        "current_stock": inv.current_stock,
        "predicted_7d_demand": round(predicted_7d, 2),
        "predicted_target_demand": round(predicted_target_demand, 2),
        "safety_stock": round(safety_stock, 2),
        "gross_requirement": round(gross_requirement, 2),
        "recommended_restock_quantity": recommended_restock,
        "urgency": urgency,
        "historical_stats": {
            "demand_today": ts_features["demand_today"],
            "lag_1": ts_features["lag_1"],
            "lag_7": ts_features["lag_7"],
            "lag_14": ts_features["lag_14"],
            "lag_28": ts_features["lag_28"],
            "roll_mean_7d": round(ts_features["roll_mean_7"], 2),
            "roll_std_7d": round(ts_features["roll_std_7"], 2),
        }
    }