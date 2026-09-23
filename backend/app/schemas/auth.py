# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: EmailStr | None = None
    roles: List[str] = []

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    roles: List[str]
