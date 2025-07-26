import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr
from config.base_config import APP_CONFIG

security = HTTPBearer()
SECRET_KEY = APP_CONFIG.auth_config.key
ALGORITHM = APP_CONFIG.auth_config.algorithm
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
        email: EmailStr = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id, email, or role")
            
        return {"user_id": user_id, "email": email, "role": role}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def require_user_role(current_user: dict = Depends(get_current_user)):
    """
    A dependency that ensures the current user has the 'user' role.
    """
    if current_user.get("role") != "user":
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Access is restricted to users only."
        )
    return current_user
