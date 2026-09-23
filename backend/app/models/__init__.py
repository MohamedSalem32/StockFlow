# app/models/__init__.py
from app.db import Base

# Import models so they register with Base.metadata
from app.models.user import User, Role  # noqa: F401

# If you have others:
# from app.models.product import Product  # noqa: F401
# from app.models.inventory import Inventory  # noqa: F401
# from app.models.supplier import Supplier  # noqa: F401
# from app.models.purchase_order import PurchaseOrder, POLine  # noqa: F401
 