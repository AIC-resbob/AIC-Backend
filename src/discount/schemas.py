from pydantic import BaseModel, Field
from typing import Optional, List

class DiscountRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product in the database")
    current_date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD), defaults to today")
    target_days: Optional[int] = Field(7, description="Number of days to evaluate inventory clearance")
    selling_price: Optional[float] = Field(None, description="Selling price overrides")
    cogs: Optional[float] = Field(None, description="COGS overrides")

class CandidateEvaluation(BaseModel):
    discount_pct: float
    discounted_price: float
    margin_per_unit: float
    predicted_daily_demand: float
    expected_units_sold: float
    expected_profit: float

class DiscountResponse(BaseModel):
    product_id: int
    product_name: str
    category: str
    original_price: float
    cogs: float
    current_stock: int
    days_to_expiry: int
    recommended_discount_pct: float
    recommended_price: float
    max_safe_discount_pct: float
    estimated_units_sold: float
    estimated_profit: float
    status: str
    evaluation_candidates: List[CandidateEvaluation]