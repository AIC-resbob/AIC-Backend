from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from db_models import Product, Inventory, User
from auth.utils import get_current_user
from discount.schemas import DiscountRequest, DiscountResponse
from discount.service import recommend_optimal_discount

router = APIRouter(prefix="/api", tags=["Discount Engine"])

@router.post("/recommend-discount", response_model=DiscountResponse)
async def get_discount_recommendation(
    payload: DiscountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch product with joined inventory
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product or not product.inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {payload.product_id} or its inventory records were not found."
        )

    inv: Inventory = product.inventory
    eval_date = None
    if payload.current_date:
        try:
            eval_date = datetime.strptime(payload.current_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD."
            )
    price_to_use = payload.selling_price if payload.selling_price is not None else inv.selling_price
    cogs_to_use = payload.cogs if payload.cogs is not None else inv.cogs

    result = recommend_optimal_discount(
        product_id=product.id,
        kategori=product.category,
        selling_price=price_to_use,
        cogs=cogs_to_use,
        current_stock=inv.current_stock,
        days_to_expiry=inv.days_to_expire,
        eval_date=eval_date,
        target_days=payload.target_days
    )

    return {
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category,
        "original_price": price_to_use,
        "cogs": cogs_to_use,
        "current_stock": inv.current_stock,
        "days_to_expiry": inv.days_to_expire,
        **result
    }