import jwt
import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from dotenv import load_dotenv
from .config_auth import AuthenConfig
load_dotenv()

security = HTTPBearer()

SECRET_KEY = AuthenConfig().key
ALGORITHM = AuthenConfig().algorithm

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token from the Authorization header and return user details.
    This function is designed to be used as a dependency in FastAPI routes.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None or role is None:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token: missing user_id, email, or role"
            )
            
        return {
            "user_id": user_id, 
            "email": email, 
            "role": role
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def require_staff_or_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    A dependency that ensures the current user has 'staff' or 'admin' role.
    Used for prediction APIs that require elevated access.
    """
    user_role = current_user.get("role")
    if user_role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Access is restricted to staff and admin users only."
        )
    return current_user

def require_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    A dependency that ensures the current user has the 'admin' role.
    Used for training APIs that require admin access only.
    """
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Access is restricted to admin users only."
        )
    return current_user

