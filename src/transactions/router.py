from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from db_models import Transaction, Inventory, User
from auth.utils import get_current_user
from transactions.schemas import TransactionCreate, TransactionResponse
from typing import Optional
router = APIRouter(prefix="/api", tags=["Transactions (POS)"])

@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Transaction).order_by(Transaction.transaction_date.desc())
    if product_id:
        query = query.filter(Transaction.product_id == product_id)
    return query.limit(limit).all()

@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def record_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Inventory).filter(Inventory.product_id == payload.product_id).first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Product with ID {payload.product_id} has no inventory record."
        )

    if inv.current_stock < payload.quantity_sold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {inv.current_stock}, requested: {payload.quantity_sold}"
        )

    # Deduct stock atomically
    inv.current_stock -= payload.quantity_sold

    new_tx = Transaction(
        product_id=payload.product_id,
        quantity_sold=payload.quantity_sold,
        discount_applied=payload.discount_applied,
        transaction_date=datetime.utcnow()
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)

    return new_tx