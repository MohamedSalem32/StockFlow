from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.db import get_db

from app.models_base import Supplier

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SupplierIn(BaseModel):
    org_id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class SupplierOut(SupplierIn):
    id: int
    class Config:
        from_attributes = True

@router.post("", response_model=SupplierOut)
def create_supplier(payload: SupplierIn, db: Session = Depends(get_db)):
    exists = db.query(Supplier).filter(
        Supplier.org_id == payload.org_id, Supplier.name == payload.name
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Supplier name already exists in this org")
    obj = Supplier(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("", response_model=List[SupplierOut])
def list_suppliers(org_id: int, db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.org_id == org_id).order_by(Supplier.name.asc()).all()
