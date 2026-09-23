from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from app.db import SessionLocal
from app.db import get_db

from app.models_base import Inventory, Product

router = APIRouter(prefix="/inventory", tags=["inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AdjustIn(BaseModel):
    product_id: int
    delta: Decimal
    location: str = "MAIN"

@router.post("/adjust")
def adjust_stock(payload: AdjustIn, db: Session = Depends(get_db)):
    prod = db.get(Product, payload.product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    rec = db.query(Inventory).filter(
        Inventory.product_id == payload.product_id,
        Inventory.location == payload.location
    ).first()

    if not rec:
        rec = Inventory(product_id=payload.product_id, location=payload.location, quantity=Decimal("0"))
        db.add(rec)

    new_q = (rec.quantity or Decimal("0")) + payload.delta
    if new_q < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot go negative")

    rec.quantity = new_q
    db.commit(); db.refresh(rec)
    return {"product_id": rec.product_id, "location": rec.location, "quantity": str(rec.quantity)}
