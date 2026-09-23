# backend/app/db/__init__.py
from .database import Base, engine, SessionLocal
from .database import get_db   # noqa: F401  
# if you also want db_session available everywhere:
# from .database import db_session
