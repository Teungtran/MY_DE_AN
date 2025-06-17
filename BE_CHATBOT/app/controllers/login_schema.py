from orchestrator.graph.tools.support_nodes import connect_to_db
from config.base_config import APP_CONFIG
import re
from pydantic import BaseModel, field_validator
from typing import List, Optional


# Pydantic models
class RegisterRequest(BaseModel):
    customer_name: str
    address: str
    age: int
    customer_phone: str
    password: str
    preference_brand: Optional[List[str]] = None
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    
    @field_validator('customer_phone')
    def validate_phone_number(cls, v):
        """Validate Vietnamese phone number format"""
        phone = re.sub(r'[\s-]', '', v)
        mobile_pattern = r'^(09|03|05|07|08)[0-9]{8}$'
        landline_pattern = r'^[0-9]{10}$'
        if not (re.match(mobile_pattern, phone) or re.match(landline_pattern, phone)):
            raise ValueError('Invalid Vietnamese phone number format')
        
        return phone
    
    @field_validator('password')
    def validate_password(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class LoginRequest(BaseModel):
    customer_name: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

