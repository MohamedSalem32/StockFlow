# app/models.py
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db import Base


# ------------ Core ------------
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)

    # optional: backrefs
    products = relationship("Product", cascade="all,delete-orphan", backref="organization")
    suppliers = relationship("Supplier", cascade="all,delete-orphan", backref="organization")
    purchase_orders = relationship("PurchaseOrder", cascade="all,delete-orphan", backref="organization")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # If you want SKUs unique per organization (recommended for multi-tenant), use the constraint below
    sku = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    unit = Column(String(32), default="unit")
    barcode = Column(String(128))

    __table_args__ = (
        UniqueConstraint("org_id", "sku", name="uq_product_org_sku"),
        Index("ix_product_name", "name"),
    )

    inventory_records = relationship("Inventory", cascade="all,delete-orphan", backref="product")
    po_items = relationship("PurchaseOrderItem", backref="product")


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    location = Column(String(64), default="MAIN")
    # Use fixed precision for quantities
    quantity = Column(Numeric(18, 2), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("product_id", "location", name="uq_inventory_product_location"),
        Index("ix_inventory_location", "location"),
    )

# ------------ Suppliers ------------
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_supplier_org_name"),)

    purchase_orders = relationship("PurchaseOrder", backref="supplier")

# ------------ Purchase Orders ------------
class POStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    RECEIVED = "RECEIVED"
    CANCELED = "CANCELED"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum(POStatus), default=POStatus.DRAFT, nullable=False)
    notes = Column(Text, nullable=True)
    expected_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("PurchaseOrderItem", cascade="all, delete-orphan", backref="po")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 2), nullable=False)
    unit_price = Column(Numeric(18, 2), nullable=True)
