from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransactionCreate(BaseModel):
    product_id: int = Field(..., description="ID of the product sold")
    quantity_sold: int = Field(..., gt=0, description="Number of units sold")
    discount_applied: Optional[float] = Field(0.0, ge=0.0, description="Discount amount or fraction applied")

class TransactionResponse(BaseModel):
    id: int
    product_id: int
    quantity_sold: int
    discount_applied: float
    transaction_date: datetime

    class Config:
        from_attributes = True