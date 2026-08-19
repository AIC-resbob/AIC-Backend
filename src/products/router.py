from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from db_models import Product, Inventory, User
from auth.utils import get_current_user
from products.schemas import (
    ProductCreate,
    ProductResponse,
    InventoryUpdate,
    InventoryResponse,
    DashboardOverviewResponse,
    DashboardOverviewItem,
)

router = APIRouter(prefix="/api", tags=["Products & Inventory"])

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.all()

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = Product(name=payload.name, category=payload.category)
    db.add(product)
    db.flush()

    inv = Inventory(
        product_id=product.id,
        current_stock=payload.inventory.current_stock,
        cogs=payload.inventory.cogs,
        selling_price=payload.inventory.selling_price,
        days_to_expire=payload.inventory.days_to_expire
    )
    db.add(inv)
    db.commit()
    db.refresh(product)
    return product

@router.patch("/inventory/{product_id}", response_model=InventoryResponse)
async def update_inventory(
    product_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inv, key, value)

    db.commit()
    db.refresh(inv)
    return inv

@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    products = db.query(Product).all()
    
    total_val = 0.0
    low_stock = 0
    expiring = 0
    items = []

    for p in products:
        if not p.inventory:
            continue
        inv = p.inventory
        
        is_low = inv.current_stock <= 15
        is_exp = inv.days_to_expire <= 14

        if is_low:
            low_stock += 1
        if is_exp:
            expiring += 1

        total_val += (inv.current_stock * inv.cogs)

        items.append(DashboardOverviewItem(
            id=p.id,
            name=p.name,
            category=p.category,
            current_stock=inv.current_stock,
            selling_price=inv.selling_price,
            cogs=inv.cogs,
            days_to_expire=inv.days_to_expire,
            is_low_stock=is_low,
            is_expiring_soon=is_exp
        ))

    return {
        "total_products": len(products),
        "total_inventory_value": round(total_val, 2),
        "low_stock_count": low_stock,
        "expiring_soon_count": expiring,
        "items": items
    }