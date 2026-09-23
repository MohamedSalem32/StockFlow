# backend/app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM
from app.schemas.auth import TokenData

bearer = HTTPBearer()

def get_current_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> TokenData:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(sub=payload.get("sub"), roles=payload.get("roles", []))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def role_required(allowed: list[str]):
    def _dep(token: TokenData = Depends(get_current_token)):
        if not set(token.roles).intersection(set(allowed)):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return token
    return _dep
