from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from db_models import Product, User
from auth.utils import get_current_user
from restock.schemas import RestockRequest, RestockResponse
from restock.service import forecast_restock

router = APIRouter(prefix="/api", tags=["Restock Predictor"])

@router.post("/predict-restock", response_model=RestockResponse)
async def get_restock_prediction(
    payload: RestockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product or not product.inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {payload.product_id} or its inventory records were not found."
        )

    eval_date = None
    if payload.eval_date:
        try:
            eval_date = datetime.strptime(payload.eval_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD."
            )

    return forecast_restock(
        db=db,
        product=product,
        inv=product.inventory,
        eval_date=eval_date,
        target_days=payload.target_days or 7,
        service_level_z=payload.service_level_z
    )