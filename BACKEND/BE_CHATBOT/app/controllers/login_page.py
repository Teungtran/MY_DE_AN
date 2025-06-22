from sqlalchemy import text
from orchestrator.graph.tools.support_nodes import connect_to_db
from config.base_config import APP_CONFIG
import json
import uuid
import base64
from fastapi import HTTPException, Depends, APIRouter, status
import re
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
from .login_schema import RegisterRequest, LoginRequest, AuthResponse, PasswordChangeRequest
from utils.email import send_email
import string
from random import choices
from sqlalchemy.orm import Session
from models.database import CustomerInfo, get_db

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

def is_valid_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

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


def check_phone_exists(phone: str, db: Session) -> bool:
    """Check if phone number already exists in database"""
    return db.query(CustomerInfo).filter(CustomerInfo.customer_phone == phone).first() is not None

def check_email_exists(email: str, db: Session) -> bool:
    """Check if email already exists in database"""
    return db.query(CustomerInfo).filter(CustomerInfo.email == email).first() is not None

def login(identifier: str, password: str, db: Session):
    """Login user with password verification"""
    user = db.query(CustomerInfo).filter(
        (CustomerInfo.customer_name == identifier) | (CustomerInfo.email == identifier)
    ).first()
    if not is_valid_email(CustomerInfo.email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email"
        )
    if user and verify_password(password, user.password):
        return {
            "user_id": user.user_id,
            "email": user.email
        }
    return None

def register_new_user(
    customer_name: str, 
    address: str, 
    age: int, 
    customer_phone: str, 
    password: str,
    db: Session,
    preference_brand: List[str] = None, 
    min_price: str = None, 
    max_price: str = None,
    email: str = None
):
    """Register new user with validation"""
    if not is_valid_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 10 characters long, include 1 uppercase letter, 1 number, and 1 special character"
        )
    if not is_valid_email(email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email"
        )
    if check_phone_exists(customer_phone, db):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    if email and check_email_exists(email, db):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if preference_brand is None:
        preference_brand = []

    prefs = {
        "brand": preference_brand,
        "price_range": [min_price, max_price] if min_price is not None and max_price is not None else []
    }
    preferences_json = json.dumps(prefs)
    user_id = f"USER_{generate_short_id()}"
    hashed_password = hash_password(password)

    try:
        new_user = CustomerInfo(
            user_id=user_id,
            customer_name=customer_name,
            address=address,
            preferences=preferences_json,
            age=age,
            customer_phone=customer_phone,
            password=hashed_password,
            email=email
        )
        
        db.add(new_user)
        db.commit()
        
        return {
            "user_id": user_id,
            "email": email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


def get_current_user(user_id: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current authenticated user details"""
    user = db.query(CustomerInfo).filter(CustomerInfo.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "user_id": user.user_id,
        "email": user.email
    }


@auth.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = register_new_user(
            customer_name=request.customer_name,
            address=request.address,
            age=request.age,
            customer_phone=request.customer_phone,
            password=request.password,
            db=db,
            preference_brand=request.preference_brand,
            min_price=request.min_price,
            max_price=request.max_price,
            email=request.email
        )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["user_id"]}, expires_delta=access_token_expires
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user["user_id"],
            email=user["email"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@auth.post("/login", response_model=AuthResponse)
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    user = login(request.customer_name, request.password, db)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["user_id"],
        email=user["email"]
    )

@auth.post("/forgot-password")
async def forgot_password(customer_name: str, email: str, db: Session = Depends(get_db)):
    temp_password = ''.join(choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    hashed_password = hash_password(temp_password)
    
    user = db.query(CustomerInfo).filter(
        (CustomerInfo.customer_name == customer_name) & 
        (CustomerInfo.email == email)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User with given name and email not found")
    
    user.password = hashed_password
    db.commit()

    send_email(
        to_email=email,
        subject="Your New Password",
        body=f"Hello {customer_name},\n\nYour temp password is: {temp_password}\n\nPlease change by click change password."
    )

    return {"message": "A new temp password has been sent to your email."}

@auth.post("/change-password")
async def change_password(request: PasswordChangeRequest, db: Session = Depends(get_db)):
    if not is_valid_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 10 characters long, include 1 uppercase letter, 1 number, and 1 special character"
        )
    
    hashed_password = hash_password(request.new_password)
    
    user = db.query(CustomerInfo).filter(
        (CustomerInfo.customer_name == request.customer_name) & 
        (CustomerInfo.email == request.email)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found with that name and email")
    
    user.password = hashed_password
    db.commit()

    return {"message": "Password updated successfully"}

@auth.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """Example protected route"""
    return {"message": f"Hello user {current_user['user_id']}!", "user_id": current_user["user_id"]}

