
import re
from pydantic import BaseModel, field_validator,EmailStr,Field
from typing import List
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"
    staff = "staff"
class RegisterRequest(BaseModel):
    customer_name: str
    address: str
    age: int
    customer_phone: str
    password: str
    email: EmailStr 
    preference_brand: List[str] = []
    min_price: str = None
    max_price: str = None
    role: RoleEnum = Field(default=RoleEnum.user, description="User role")

    @field_validator('customer_phone')
    def validate_phone_number(cls, v):
        """Validate Vietnamese phone number format"""
        phone = re.sub(r'[\s-]', '', v)
        mobile_pattern = r'^(09|03|08)[0-9]{8}$'
        landline_pattern = r'^[0-9]{10}$'
        if not (re.match(mobile_pattern, phone) or re.match(landline_pattern, phone)):
            raise ValueError('Invalid Vietnamese phone number format')
        
        return phone
    

class LoginRequest(BaseModel):
    customer_name_or_email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: EmailStr
    role: str

    
class PasswordChangeRequest(BaseModel):
    customer_name: str
    email: EmailStr
    temp_password: str
    new_password: str

