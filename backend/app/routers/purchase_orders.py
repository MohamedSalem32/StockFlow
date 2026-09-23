# app/routers/purchase_orders.py
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from datetime import datetime
from app.db import get_db


from app.db import SessionLocal
from app.models_base import (
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    Product,
    POStatus,
)

router = APIRouter(prefix="/purchase-orders", tags=["purchase_orders"])


# --- DB session dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Pydantic schemas ---
class POItemIn(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Optional[Decimal] = None


class POCreateIn(BaseModel):
    org_id: int
    supplier_id: int
    items: List[POItemIn]
    notes: Optional[str] = None
    expected_date: Optional[datetime] = None


class POItemOut(BaseModel):
    id: int
    product_id: int
    # serialize decimals as strings to avoid float rounding in JSON
    quantity: str
    unit_price: Optional[str] = None

    class Config:
        from_attributes = True


class POOut(BaseModel):
    id: int
    org_id: int
    supplier_id: int
    status: POStatus
    notes: Optional[str] = None
    expected_date: Optional[datetime] = None
    items: List[POItemOut]

    class Config:
        from_attributes = True


class POStatusIn(BaseModel):
    status: POStatus


# --- Helpers ---
def _load_po_with_items(db: Session, po_id: int) -> Optional[PurchaseOrder]:
    """Return a PO with items eagerly loaded."""
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == po_id)
        .first()
    )


# --- Endpoints ---

@router.post("", response_model=POOut)
def create_po(payload: POCreateIn, db: Session = Depends(get_db)):
    # Validate supplier exists (and optionally same org)
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Validate products & quantities
    product_ids = [it.product_id for it in payload.items]
    if not product_ids:
        raise HTTPException(status_code=400, detail="PO must contain at least one item")

    existing_products = (
        db.query(Product.id)
        .filter(Product.id.in_(product_ids))
        .all()
    )
    existing_ids = {pid for (pid,) in existing_products}
    missing = [pid for pid in product_ids if pid not in existing_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"Products not found: {missing}")

    if any(it.quantity <= 0 for it in payload.items):
        raise HTTPException(status_code=400, detail="Each item quantity must be > 0")

    # Create PO
    po = PurchaseOrder(
        org_id=payload.org_id,
        supplier_id=payload.supplier_id,
        status=POStatus.SUBMITTED,
        notes=payload.notes,
        expected_date=payload.expected_date,
    )
    db.add(po)
    db.flush()  # get po.id without committing yet

    # Add items
    for it in payload.items:
        db.add(
            PurchaseOrderItem(
                po_id=po.id,
                product_id=it.product_id,
                quantity=it.quantity,
                unit_price=it.unit_price,
            )
        )

    db.commit()
    db.refresh(po)

    return _load_po_with_items(db, po.id)


@router.get("", response_model=List[POOut])
def list_pos(org_id: int, db: Session = Depends(get_db)):
    pos = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.org_id == org_id)
        .order_by(PurchaseOrder.created_at.desc())
        .all()
    )
    return pos


@router.post("/{po_id}/status", response_model=POOut)
def update_status(
    po_id: int = Path(..., gt=0),
    payload: POStatusIn = None,
    db: Session = Depends(get_db),
):
    po = _load_po_with_items(db, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    po.status = payload.status
    db.commit()
    db.refresh(po)

    return _load_po_with_items(db, po_id)


# --- Optional convenience endpoint: receive a PO into stock ---
# This increases inventory for each PO item (location=MAIN by default)
# and marks the PO as RECEIVED.
class ReceiveIn(BaseModel):
    location: str = "MAIN"


@router.post("/{po_id}/receive", response_model=POOut)
def receive_po(
    po_id: int = Path(..., gt=0),
    payload: ReceiveIn = None,
    db: Session = Depends(get_db),
):
    po = _load_po_with_items(db, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    if not po.items:
        raise HTTPException(status_code=400, detail="PO has no items to receive")

    # Only allow receive if not already received/canceled
    if po.status in {POStatus.RECEIVED, POStatus.CANCELED}:
        raise HTTPException(status_code=400, detail=f"PO is already {po.status}")

    # Apply each item to inventory (direct DB update to avoid HTTP roundtrip)
    # We reuse your Inventory model logic through ORM here
    from app.models_base import Inventory  # local import to avoid circulars

    for it in po.items:
        inv = (
            db.query(Inventory)
            .filter(
                Inventory.product_id == it.product_id,
                Inventory.location == payload.location,
            )
            .first()
        )
        if not inv:
            inv = Inventory(
                product_id=it.product_id, location=payload.location, quantity=Decimal("0")
            )
            db.add(inv)

        inv.quantity = (inv.quantity or Decimal("0")) + (it.quantity or Decimal("0"))

    po.status = POStatus.RECEIVED
    db.commit()
    db.refresh(po)

    return _load_po_with_items(db, po_id)
