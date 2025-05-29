from pydantic import BaseModel
from typing import Annotated, Literal, Optional, List


class CompleteOrEscalate(BaseModel):
    """A tool to return control to the main assistant when:
    1. The current sales or support task on phones, laptops, or related devices is completed successfully.
    2. The user's question is not related to phones, laptops, or electronic devices in this agent's domain.
    3. The agent requires capabilities only available in the main assistant.
    
    ALWAYS use this tool when user asks questions outside your phones/laptops/electronics expertise.
    """

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User asked about household appliances which are not handled by the phones and laptops agent. Returning to main assistant.",
            },
            "example 2": {
                "cancel": True,
                "reason": "Successfully completed the phone and laptop or purchase request. No further assistance needed.",
            },
            "example 3": {
                "cancel": True,
                "reason": "User's question about software installation or troubleshooting unrelated to phones or laptops. Escalating to main assistant.",
            },
            "example 4": {
                "cancel": True,
                "reason": "User switched topic from phones and laptops to store policies or billing. Returning to main assistant.",
            },
            "example 5": {
                "cancel": False,
                "reason": "Need advanced technical support capabilities from the main assistant.",
            },
        }





class Order(BaseModel):
    """order based on the provided details."""

    device_name: Annotated[str, "The unique identifier for the device"]
    customer_name: Annotated[Optional[str], "The name of the customer ordering"]
    customer_phone: Annotated[Optional[str], "The phone number of the customer ordering"]
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
class RecommendationConfig:
    MAX_RESULTS = 10
    BRAND_MATCH_BOOST = 15
    PRICE_RANGE_MATCH_BOOST = 15
    TYPE_MATCH_BOOST = 5
    HISTORY_MATCH_BOOST = 10
    FUZZY_WEIGHT = 0.5
    COSINE_WEIGHT = 0.5