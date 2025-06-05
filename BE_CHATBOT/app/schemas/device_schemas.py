from pydantic import BaseModel
from typing import Annotated, Literal, Optional
from datetime import datetime

class CompleteOrEscalate(BaseModel):
    """A tool to return control to the main assistant when:
    1. The current task is completed successfully and no further assistance is needed.
    2. The user's question is completely unrelated to FPT Shop's scope (electronics, IT support, policies).
    3. The agent requires capabilities only available in the main assistant.
    
    DO NOT use this tool for:
    - Questions about FPT Shop policies (use RAG_Agent)
    - IT support questions (use it_support_agent)
    - Device maintenance and cleaning (use it_support_agent)
    - Technical troubleshooting (use it_support_agent)
    - Product recommendations (use recommend_system)
    - Order management (use order_purchase, cancel_order, track_order)
    - Store appointments (use book_appointment)
    """

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User asked about household appliances which are not handled by FPT Shop. Returning to main assistant.",
            },
            "example 2": {
                "cancel": True,
                "reason": "User asked about food delivery services which are outside FPT Shop's scope. Returning to main assistant.",
            },
            "example 3": {
                "cancel": True,
                "reason": "User asked about clothing and fashion which are not part of FPT Shop's product range. Returning to main assistant.",
            },
            "example 4": {
                "cancel": True,
                "reason": "User asked about banking services which are not provided by FPT Shop. Returning to main assistant.",
            },
            "example 5": {
                "cancel": False,
                "reason": "Need advanced capabilities from the main assistant for a complex multi-domain query.",
            }
        }





class Order(BaseModel):
    """order based on the provided details."""
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
    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "iPhone 16 Plus 128GB",
                "customer_name": "John Doe",
                "address": "EN Street, NYC, USA",
                "customer_phone": "1234567890",
                "quantity": 1,
                "shipping": True,
                "payment": "cash on delivery"
            }
        }


class CancelOrder(BaseModel):
    """Cancel order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to cancel"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "1527728287278"
            }
        }
        
class TrackOrder(BaseModel):
    """Track order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to track"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "1527728287278"
            }
        }
class BookAppointment(BaseModel):
    reason: Annotated[str, "Reason of the appointment"]
    customer_name: Optional[Annotated[str, "The name of the customer ordering"]] = None
    customer_phone: Optional[Annotated[str, "The phone number of the customer ordering"]] = None
    time: Annotated[datetime, "Time of the appointment"]
    note: Optional[Annotated[str, "Any note from customer"]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Screen repair",
                "customer_name": "John Doe",
                "customer_phone": "1234567890",
                "time": "2025-06-10T15:30:00Z",
                "note": "Prefer afternoon slot"
            }
        }
class RecommendationConfig:
    MAX_RESULTS = 8
    BRAND_MATCH_BOOST = 15
    PRICE_RANGE_MATCH_BOOST = 15
    TYPE_MATCH_BOOST = 5
    HISTORY_MATCH_BOOST = 10
    FUZZY_WEIGHT = 0.6
    COSINE_WEIGHT = 0.4