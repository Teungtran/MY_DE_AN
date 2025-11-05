from pydantic import BaseModel,EmailStr,field_validator, Field
from typing import Annotated, Literal, Optional, List
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
class UrlExtraction(BaseModel):
    """extract information from url based on user input"""

    user_input: Annotated[str, "User questions for url extraction"]
    urls: Annotated[List[str], "list of urls to extract information from"]

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "What is the product of FPT Shop?",
                "urls": "https://fptshop.com.vn"
            },
            "example2": {
                "user_input": "Compare these two products",
                "urls": ["https://fptshop.com.vn/product1", "https://fptshop.com.vn/product2"]
            }
        }
class RecommendSystem(BaseModel):
    user_input: str = Field(
        ...,
        description=(
            "the name of devices ( 1 or many ) OR what device + brand + features to search, THIS MUST BE SEPERATED BY COMMA ',' "
        )
    )
    has_features: bool = Field(
        ...,
        description="True or False if there any specific features mentioned, if user_input do not specify any requirements beside price , put False"
    )
    device_name: bool = Field(
        ...,
        description="True or False if device name or any brand like APPLE , Samsung.... exsist, if user_input do not specify any requirements beside price , put False"
    )
    device_type: Optional[
        Literal["phone", "laptop/pc", "tablet", "earphone", "mouse", "keyboard"]
    ] = Field(
        None,
        description=(
            "Categories of the electronic devices. Follow strictly this rule:\n"
            "- if user_input is related to phone/smartphone -> 'phone'\n"
            "- if related to laptop/pc/macbook -> 'laptop/pc'\n"
            "- if related to tablet/ipad -> 'tablet'\n"
            "- if related to earphone/headphone/airpod -> 'earphone'\n"
            "- if related to mouse/chuột -> 'mouse'\n"
            "- if related to keyboard -> 'keyboard'\n"
        )
    )

    price: Optional[str] = Field(
        None,
        description="Price mentioned in user_input, in VND in numeric format (e.g., '10000000' means 10 million VND), if you receive a range, take the higher price."
    )
    
    suitable_for: Optional[
        Literal["gaming/IT", "office", "students", "general"]
    ] = Field(
        None,
        description=(
            "Categories of the electronic devices. Follow strictly this rule:\n"
            "- if the 'suitable_for' in user_input == 'gaming/IT' -> 'gaming/IT'\n"
            "- if the 'suitable_for' in user_input == 'office' -> 'office'\n"
            "- if the 'suitable_for' in user_input == 'students' -> 'students'\n"
            "- if the 'suitable_for' in user_input == 'general' -> 'general'"
        )
    )

    @field_validator("suitable_for", mode="before")
    @classmethod
    def validate_suitable_for(cls, v):
        allowed_types = {
            "gaming/IT", "office", "students", "general"
        }
        if not v:
            return "general"
        v = str(v).strip()
        return v if v in allowed_types else "general"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "Laptop Asus A32",
                "device_name": True,
                "has_features": False,
                "device_type": "laptop/pc",
                "suitable_for": "gaming/IT",
                "price": "10000000"
            }
        }





class DeviceDetailSchema(BaseModel):
    user_input: str = Field(
        ...,
        description="User query for detail information"
    )

    device_name: bool = Field(
        ...,
        description="True or False if device name exsist"
    )
    count_devices: int = Field(
        ...,
        description="number of devices names in user_input"
    )
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "can you tell me more about the macbook you recommend",
                "device_name": False,
                "count_devices": 1
            }
        }
