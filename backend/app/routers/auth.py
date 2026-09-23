# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.db import Base


from app.models.user import User, Role
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    # default role: Viewer
    viewer = db.query(Role).filter(Role.name == "Viewer").first()
    if viewer: user.roles.append(viewer)
    db.add(user); db.commit(); db.refresh(user)
    return UserOut(id=user.id, email=user.email, roles=[r.name for r in user.roles])

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(400, "Incorrect email or password")
    roles = [r.name for r in user.roles]
    return Token(access_token=create_access_token(user.email, roles))
