import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.base_config import APP_CONFIG
from app.utils.db import get_db, CustomerInfo

security = HTTPBearer()
SECRET_KEY = APP_CONFIG.auth_config.key
ALGORITHM = APP_CONFIG.auth_config.algorithm

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify JWT token from the Authorization header and verify user role from database.
    This ensures RBAC is enforced even if user role changes after token issuance.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        # Verify user exists and get role from database (RBAC enforcement)
        user = db.query(CustomerInfo).filter(CustomerInfo.user_id == user_id).first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found or has been deleted")
            
        return {"user_id": user_id, "role": user.role}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def require_store_role(current_user: dict = Depends(get_current_user)):
    """
    A dependency that ensures the current user has the 'admin' or 'staff' role.
    """
    if current_user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Access is restricted to admin and staff users only."
        )
    return current_user
