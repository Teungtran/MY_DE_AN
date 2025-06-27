from pydantic import BaseModel,EmailStr,field_validator
from typing import Annotated, Literal, Optional
from datetime import datetime


class CompleteOrEscalate(BaseModel):
    """A tool to return control to the main assistant when:
    1. The current task is completed successfully and no further assistance is needed.
    2. The user's question is completely unrelated to FPT Shop's scope (electronics, IT support, policies).
    3. The agent requires capabilities only available in the main assistant.
    4. The user attempts to confirm an action (e.g., by typing 'y' or 'n') rather than providing substantive input.
    5. The user tries to modify content or input parameters after a tool call has been initiated or is pending confirmation.

    Use this tool to gracefully hand back the conversation to the assistant in cases of ambiguous, off-topic, or low-signal input that suggests a need for higher-level clarification or handling.
    """

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            
            "example 3": {
                "cancel": False,
                "reason": "I need to ask the user again for more information.",
            },
            "example 4": {
                "cancel": True,
                "reason": "User typed 'y' to confirm, which should be handled by the main assistant.",
            },
            "example 5": {
                "cancel": True,
                "reason": "User is trying to change input content after the tool was called.",
            },
            
        }




class Order(BaseModel):
    device_name: Annotated[str, "The unique identifier for the device"]
    customer_name: Annotated[Optional[str], "The name of the customer ordering"]
    customer_phone: Annotated[Optional[str], "The phone number of the customer ordering"]
    time: Annotated[Optional[datetime], "The time customer want the product to be delievered or time for pickup"]
    address: Annotated[Optional[str], "The address of the customer ordering"]
    quantity: Annotated[int, "number of purchase"]
    shipping: Annotated[Optional[bool], "shipping or not shipping"]
    payment: Annotated[
        Optional[Literal["pay later", "bank transfer", "cash on delivery"]],
        "Payment method: 'pay later', 'bank transfer', or 'cash on delivery'"
    ]
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]
    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "iPhone 16 Plus 128GB",
                "customer_name": "John Doe",
                "address": "EN Street, NYC, USA",
                "customer_phone": "1234567890",
                "quantity": 1,
                "shipping": True,
                "payment": "cash on delivery",
                "user_id": "user333232",
                "email": "jdoe@en.com"
            }
        }
class UpdateOrder(BaseModel):
    order_id: Annotated[str, "The unique identifier for the order"]
    device_name: Optional[Annotated[str, "The updated device_name"]] = None
    customer_name: Optional[Annotated[str, "The updated name of the customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The updated phone number of the customer ordering"]] = None
    time: Annotated[Optional[datetime], "The updated time customer want the product to be delievered or time for pickup"]
    address: Optional[Annotated[str, "The updated address of the customer ordering"]] = None
    quantity: Optional[Annotated[str, "The updated number of purchase"]] = None
    shipping: Optional[Annotated[str, "update shipping or not shipping"]] = None
    payment: Annotated[
        Optional[Literal["pay later", "bank transfer", "cash on delivery"]],
        "New updated payment method: 'pay later', 'bank transfer', or 'cash on delivery'"
    ]
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORDER-A1B2C3D4-20250610153000",
                "device_name": "iPhone 16 Plus 128GB",
                "customer_name": "John Doe",
                "address": "EN Street, NYC, USA",
                "customer_phone": "1234567890",
                "quantity": 1,
                "shipping": True,
                "payment": "cash on delivery",
                "user_id": "user333232",
                "email": "jdoe@en.com"
            }
        }

class CancelOrder(BaseModel):
    """Cancel order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to cancel"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORDER-A1B2C3D4-20250610153000",
                "email": "jdoe@en.com"
            }
        }
        
class TrackOrder(BaseModel):
    """Track order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to track"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORDER-A1B2C3D4-20250610153000"
            }
        }
class BookAppointment(BaseModel):
    reason: Annotated[str, "Reason of the appointment"]
    customer_name: Optional[Annotated[str, "The name of the customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The phone number of the customer ordering"]] = None
    time: Annotated[datetime, "Time of the appointment"]
    note: Optional[Annotated[str, "Any note from customer"]] = None
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Screen repair",
                "customer_name": "John Doe",
                "customer_phone": "1234567890",
                "time": "2025-06-10T15:30:00Z",
                "note": "Prefer afternoon slot",
                "user_id": "user333232",
                "email": "jdoe@en.com"

            }
        }
class UpdateAppointment(BaseModel):
    booking_id: Annotated[str, "The unique identifier for the appointment to update"]
    reason: Optional[Annotated[str, "new updated reason of the appointment"]] = None
    customer_name: Optional[Annotated[str, "The name of the new updated customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The phone number of the new updated customer ordering"]] = None
    time: Optional[Annotated[str, "Time of the new updated appointment"]] = None
    note: Optional[Annotated[str, "Any new updated note from customer"]] = None
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "BOOKING-A1B2C3D4-20250610153000",
                "reason": "Screen repair",
                "customer_name": "John Doe",
                "customer_phone": "1234567890",
                "time": "2025-06-10T15:30:00Z",
                "note": "Prefer afternoon slot",
                "user_id": "user333232",
                "email": "jdoe@en.com"

            }
        }
class CancelAppointment(BaseModel):
    """Cancel appointment by its appointment ID."""

    booking_id: Annotated[str, "The unique identifier for the appointment to cancel"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "BOOKING-A1B2C3D4-20250610153000",
                "email": "jdoe@en.com"
            }
        }
class TrackAppointment(BaseModel):
    """Track appointment by its appointment ID."""

    booking_id: Annotated[str, "The unique identifier for the appointment to track"]

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "BOOKING-A1B2C3D4-20250610153000"
            }
        }
        
class SendTicket(BaseModel):
    content: Annotated[str, "content of the ticket"]
    description: Optional[Annotated[str, "A short description of the ticket (less than 50 characters)"]] = None
    customer_name: Optional[Annotated[str, "The name of the customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The phone number of the customer ordering"]] = None
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "content": "I need help fixing my laptop screen",
                "description": "Screen Error",
                "customer_name": "John Doe",
                "customer_phone": "1234567890",
                "user_id": "user333232",
                "email": "jdoe@en.com"
            }
        }
class UpdateTicket(BaseModel):
    ticket_id: Annotated[str, "The unique identifier for the ticket to update"]
    content:   Optional[Annotated[str, "content of the new updated ticket"]] = None
    description: Optional[Annotated[str, "A short description of the new updated ticket (less than 50 characters)"]] = None
    customer_name: Optional[Annotated[str, "The name of the new updated customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The phone number of new updated the customer ordering"]] = None
    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TICKET-A1B2C3D4-20250610153000",
                "content": "I need help fixing my laptop screen",
                "description": "Screen Error",
                "customer_name": "John Doe",
                "customer_phone": "1234567890",
                "user_id": "user333232",
                "email": "jdoe@en.com"
            }
        }
class CancelTicket(BaseModel):
    """Cancel appointment by its appointment ID."""

    ticket_id: Annotated[str, "The unique identifier for the ticket to cancel"]
    email: Annotated[EmailStr,"The email of the customer ordering"]

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TICKET-A1B2C3D4-20250610153000",
                "email": "jdoe@en.com"
            }
        }
class TrackTicket(BaseModel):
    """Track appointment by its appointment ID."""

    ticket_id: Annotated[str, "The unique identifier for the ticket to track"]

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TICKET-A1B2C3D4-20250610153000"
            }
        }
recommended_devices_cache = []

class RecommendSystem(BaseModel):
    """Recommend products based on user input and preferences."""

    user_input: Annotated[str, "User query text for recommendations"]

    type: Annotated[
        Optional[
            Literal["phone", "laptop/pc", "earphone", "mouse", "keyboard"]
        ],
        "Category of the electronic device. Follow strictly this rule: "
        "if user_input is related to phone, smartphone, category == 'phone'; "
        "if user_input is related to laptop or pc, category == 'laptop/pc'; "
        "if user_input is related to earphone, tai nghe, category == 'earphone'; "
        "if user_input is related to mouse, chuột, category == 'mouse'; "
        "if user_input is related to keyboard, bàn phím, category == 'keyboard'. "
        "if user_input does not mention any types or mentions many types (like both phone and laptop), category == None."
    ] = None

    user_id: Annotated[str, "The unique identifier for the user, always store in 'AgenticState'"]

    price: Optional[Annotated[str, "Price in VND in number format"]]

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        allowed_types = {"phone", "laptop/pc", "earphone", "mouse", "keyboard"}
        return v if v in allowed_types else None

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "I need a good smartphone",
                "type": "phone",
                "user_id": "user333232",
                "price": "10000000"
            }
        }


class RecommendationConfig:
    DEFAULT_RESULTS = 4  
    MAX_RESULTS_BY_TYPE = {
        "phone": 5,
        "laptop/pc": 5,
        "earphone": 4,
        "mouse": 3,
        "keyboard": 4,
    } 
    BRAND_MATCH_STRONG = 35
    BRAND_MATCH_MEDIUM = 25
    BRAND_MATCH_WEAK = 15
    BRAND_MISMATCH_PENALTY = -10
    PRICE_RANGE_MATCH_BOOST = 25
    FUZZY_WEIGHT = 0.4
    COSINE_WEIGHT = 0.6
    @classmethod
    def get_max_results(cls, type_):
        if not type_:
            return cls.DEFAULT_RESULTS
        return cls.MAX_RESULTS_BY_TYPE.get(type_.lower(), cls.DEFAULT_RESULTS)