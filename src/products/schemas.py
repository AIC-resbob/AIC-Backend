from pydantic import BaseModel, Field
from typing import Optional, List

class InventoryBase(BaseModel):
    current_stock: int = Field(..., ge=0)
    cogs: float = Field(..., gt=0, description="Cost of Goods Sold / Modal")
    selling_price: float = Field(..., gt=0, description="Retail selling price")
    days_to_expire: int = Field(..., ge=0)

class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = Field(None, ge=0)
    cogs: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    days_to_expire: Optional[int] = Field(None, ge=0)

class InventoryResponse(InventoryBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    inventory: InventoryBase

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    inventory: Optional[InventoryResponse] = None

    class Config:
        from_attributes = True

class DashboardOverviewItem(BaseModel):
    id: int
    name: str
    category: str
    current_stock: int
    selling_price: float
    cogs: float
    days_to_expire: int
    is_low_stock: bool
    is_expiring_soon: bool

class DashboardOverviewResponse(BaseModel):
    total_products: int
    total_inventory_value: float
    low_stock_count: int
    expiring_soon_count: int
    items: List[DashboardOverviewItem]