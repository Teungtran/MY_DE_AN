from sqlalchemy import text
from orchestrator.graph.tools.support_nodes import connect_to_db
from config.base_config import APP_CONFIG
import json
import uuid
import base64
from fastapi import HTTPException, Depends,APIRouter,status
import re
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
from .login_schema import RegisterRequest,LoginRequest,AuthResponse

sql_config = APP_CONFIG.sql_config
db = connect_to_db(server="DESKTOP-LU731VP\\SQLEXPRESS", database="CUSTOMER_SERVICE")
auth_config = APP_CONFIG.auth_config
SECRET_KEY = auth_config.key
ALGORITHM = auth_config.algorithm

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI setup
auth = APIRouter()
security = HTTPBearer()
def generate_short_id():
    uid = uuid.uuid4()
    short_id = base64.urlsafe_b64encode(uid.bytes).decode('utf-8').rstrip('=')
    return short_id[:9]
def is_valid_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 10:
        return False
    if not re.search(r"[A-Z]", password):  # at least one uppercase
        return False
    if not re.search(r"\d", password):     # at least one digit
        return False
    if not re.search(r"[^\w\s]", password):  # at least one special character
        return False
    return True
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_password_exists(password: str) -> bool:
    """Check if password already exists in database"""
    query = text("SELECT COUNT(*) FROM Customer_info WHERE password = :password")
    with db._engine.connect() as conn:
        result = conn.execute(query, {"password": password}).fetchone()
        return result[0] > 0

def check_phone_exists(phone: str) -> bool:
    """Check if phone number already exists in database"""
    query = text("SELECT COUNT(*) FROM Customer_info WHERE customer_phone = :phone")
    with db._engine.connect() as conn:
        result = conn.execute(query, {"phone": phone}).fetchone()
        return result[0] > 0

def login(customer_name: str, password: str):
    """Login user with password verification"""
    query = text("SELECT user_id, password FROM Customer_info WHERE customer_name = :customer_name")
    with db._engine.connect() as conn:
        result = conn.execute(query, {"customer_name": customer_name}).fetchone()
        if result and verify_password(password, result[1]):
            return result[0]
    return None

def register_new_user(customer_name: str, address: str, age: int, customer_phone: str, password: str,
                    preference_brand: List[str] = None, min_price: str = None, max_price: str = None):
    """Register new user with validation"""
    if not is_valid_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 10 characters long, include 1 uppercase letter, 1 number, and 1 special character"
        )
    if check_phone_exists(customer_phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    if check_password_exists(password):
        raise HTTPException(status_code=400, detail="Password already in use, please choose a different one")
    
    if preference_brand is None:
        preference_brand = []

    prefs = {
        "brand": preference_brand,
        "price_range": [min_price, max_price] if min_price is not None and max_price is not None else []
    }
    preferences_json = json.dumps(prefs)
    user_id = f"USER_{generate_short_id()}"
    hashed_password = hash_password(password)

    insert_query = text("""
        INSERT INTO Customer_info (user_id, customer_name, address, preferences, age, customer_phone, password)
        VALUES (:user_id, :customer_name, :address, :preferences, :age, :customer_phone, :password)
    """)

    try:
        with db._engine.connect() as conn:
            conn.execute(insert_query, {
                "user_id": user_id,
                "customer_name": customer_name,
                "address": address,
                "preferences": preferences_json,
                "age": age,
                "customer_phone": customer_phone,
                "password": hashed_password
            })
            conn.commit()
        return user_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")



def get_current_user(user_id: str = Depends(verify_token)):
    """Get current authenticated user details"""
    query = text("SELECT user_id, customer_name, preferences FROM Customer_info WHERE user_id = :user_id")
    with db._engine.connect() as conn:
        result = conn.execute(query, {"user_id": user_id}).fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return {
            "user_id": result[0],
            "customer_name": result[1],
            "preferences": json.loads(result[2]) if result[2] else {}
        }



@auth.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        user_id = register_new_user(
            customer_name=request.customer_name,
            address=request.address,
            age=request.age,
            customer_phone=request.customer_phone,
            password=request.password,
            preference_brand=request.preference_brand,
            min_price=request.min_price,
            max_price=request.max_price
        )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@auth.post("/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """Login user"""
    user_id = login(request.customer_name, request.password)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id
    )

@auth.get("/protected")
async def protected_route(current_user: str = Depends(verify_token)):
    """Example protected route"""
    return {"message": f"Hello user {current_user}!", "user_id": current_user}

