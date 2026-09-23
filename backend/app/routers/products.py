from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models_base import Product
from app.db import get_db


router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProductIn(BaseModel):
    org_id: int
    sku: str
    name: str
    unit: str = "unit"

class ProductOut(BaseModel):
    id: int
    org_id: int
    sku: str
    name: str
    unit: str
    barcode: str | None = None
    class Config:
        from_attributes = True

@router.post("", response_model=ProductOut)
def create_product(payload: ProductIn, db: Session = Depends(get_db)):
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    obj = Product(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
