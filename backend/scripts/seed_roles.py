# backend/scripts/seed_roles.py
from app.models.user import Role, User
from app.core.security import hash_password
from app.db import SessionLocal, db_session


def seed():
    with db_session() as db:
        # Roles
        for name in ["Admin", "Storekeeper", "Supplier", "Viewer"]:
            if not db.query(Role).filter_by(name=name).first():
                db.add(Role(name=name))

        # Admin user
        admin = db.query(User).filter_by(email="admin@local").first()
        if not admin:
            admin = User(email="admin@local", hashed_password=hash_password("admin"))
            admin_role = db.query(Role).filter_by(name="Admin").one()
            admin.roles = [admin_role]
            db.add(admin)

if __name__ == "__main__":
    seed()
