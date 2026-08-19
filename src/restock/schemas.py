from pydantic import BaseModel, Field
from typing import Optional


class RestockRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product to forecast")
    eval_date: Optional[str] = Field(None, description="Reference ISO date (YYYY-MM-DD), defaults to today")
    service_level_z: Optional[float] = Field(None, description="Custom Z-score (defaults to metadata: 1.28 for ~90% service level)")


class HistoricalStats(BaseModel):
    demand_today: float
    lag_1: float
    lag_7: float
    lag_14: float
    lag_28: float
    roll_mean_7d: float
    roll_std_7d: float


class RestockResponse(BaseModel):
    product_id: int
    product_name: str
    category: str
    current_stock: int
    predicted_7d_demand: float
    safety_stock: float
    gross_requirement: float
    recommended_restock_quantity: int
    urgency: str
    historical_stats: HistoricalStats