from pydantic import BaseModel
from typing import Annotated, Literal, Optional


class CompleteOrEscalate(BaseModel):
    """A tool to return control to the main assistant when:
    1. The current task is completed successfully
    2. The user's question is not related to this agent's core responsibilities
    3. The agent needs capabilities only available in the main assistant
    
    ALWAYS use this tool when user asks questions outside your domain expertise.
    """

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User asked about flight booking which is not handled by the tour agent. Returning to main assistant.",
            },
            "example 2": {
                "cancel": True,
                "reason": "Successfully completed the tour information request. No further tour assistance needed.",
            },
            "example 3": {
                "cancel": True,
                "reason": "User's question about visa requirements is outside this agent's expertise. Escalating to main assistant.",
            },
            "example 4": {
                "cancel": True,
                "reason": "User changed topic from tours to general company policies. Returning to main assistant.",
            },
            "example 5": {
                "cancel": False,
                "reason": "Need advanced search capabilities from the main system.",
            },
        }


class SearchTourProgram(BaseModel):
    """Search for tour programs based on various criteria."""

    query: Annotated[str, "Information about the tour program the user is asking for"]

    departure: Annotated[
        Optional[Literal[
            "ho chi minh city", "hanoi", "da nang", "nha trang", 
            "can tho", "binh duong", "buon ma thuot", "ca mau", "da lat", 
            "dong nai", "hai phong", "hue", "long xuyen", "phu quoc", 
            "quang ngai", "quang ninh", "quy nhon", "rach gia", "soc trang", 
            "tay ninh", "thai nguyen", "thanh hoa", "vinh", "vung tau"
        ]],
        "The departure location for the tour. If not specified, all types are considered."
    ] = None
    
    destination: Annotated[
        Optional[Literal[
            "ninh thuan", "nghe an", "phu yen", "cao bang", 
            "bac kan", "thanh hoa", "son la", "ca mau", "quy nhon", 
            "dien bien", "ben tre", "con dao", "kien giang", "binh thuan", 
            "ha tinh", "quang ninh", "ho chi minh city", "quang ngai", "dong thap", 
            "vinh phuc", "tay ninh", "bac lieu", "tra vinh", "long an", 
            "yen bai", "nam dinh", "thai binh", "hanoi", "hai phong", 
            "ha long", "bac ninh", "phu tho", "dak nong", "can gio", 
            "ninh binh", "ha nam", "hoa binh", "binh duong", "binh phuoc", 
            "lang son", "nam du", "tuyen quang", "lao cai", "gia lai", 
            "lam dong", "quang tri", "quang binh", "phuoc hai", "hoi an", 
            "khanh hoa", "da nang", "quang nam", "nha trang", "da lat", 
            "buon ma thuot", "kon tum", "pleiku", "phan thiet", "dong nai", 
            "ba ria - vung tau", "phu quoc", "tien giang", "can tho", "vinh long", 
            "soc trang", "ha tien", "binh dinh", "an giang", "singapore", 
            "brunei", "russia", "south korea", "taiwan", "indonesia", 
            "israel", "laos", "canada", "new zealand", "myanmar", 
            "mongolia", "australia", "philippines", "nepal", "cruise tour", 
            "cuba", "brazil", "argentina", "chile", "usa", 
            "maldives", "kazakhstan", "egypt", "mauritius", "france", 
            "south africa", "greece", "norway", "denmark", "sweden", 
            "finland", "slovakia", "portugal", "scotland", "turkey", 
            "poland", "hungary", "czech republic", "italy", "spain", 
            "netherlands", "germany", "belgium", "england", "austria", 
            "luxembourg", "monaco", "tibet", "peru", "kenya", 
            "sri lanka", "jordan", "malta", "panama", "mexico", 
            "north korea", "bhutan", "slovenia", "croatia", "madagascar", 
            "uzbekistan", "bosnia and herzegovina", "serbia", "iran", "uae", 
            "abu dhabi", "morocco", "azerbaijan", "georgia", "romania", 
            "bulgaria", "albania", "north macedonia", "pakistan", "qatar", 
            "liechtenstein", "san marino", "iceland", "zambia", "guangxi", 
            "pretoria", "chefchaouen", "sydney", "gold coast", "tasmania", 
            "perth", "blue mountain", "canberra", "dandenong", "melbourne", 
            "adelaide", "chicago", "ireland", "cambodia", "china", 
            "hong kong & macau", "thailand", "malaysia", "japan", "india"
        ]],
        "The destination location for the tour. If not specified, all types are considered."
    ] = None
    
    from_date: Annotated[Optional[str], "The starting date of the tour in 'yyyy-mm-dd' format"] = None
    
    tour_line: Annotated[
        Optional[Literal["luxury", "standard", "economy", "best price"]], 
        "The category of tour service quality. If not specified, all types are considered."
    ] = None
    
    trans_type: Annotated[
        Optional[Literal["motorcycle", "airplane"]], 
        "The primary mode of transportation for the tour. If not specified, all types are considered."
    ] = None
    
    tour_program_code: Annotated[Optional[str], "Unique identifier code for the tour program"] = None
    
    price_from: Annotated[Optional[float], "Budget of user"] = None
    
    duration: Annotated[Optional[str], "Duration of the tour (e.g., '4N3D' for 4 nights 3 days)"] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                # "query": "tôi muốn tìm tour đi hồng kông",
                "departure": "ho chi minh city",
                "destination": "hong kong & macau",
                # "from_date": "2025-06-15",
                "tour_line": "luxury",
                "trans_type": "airplane",
                "tour_program_code": "NNSGN87",
                # "price_from": 44990000,
                # "duration": "4N3D",
            }
        }


class TourProgramDetail(BaseModel):
    """Retrieve detailed information for a specific tour program."""

    query: Annotated[str, "Information about the tour program the user is asking for"]

    tour_program_code: Annotated[str, "Unique identifier code for the tour program"]

    class Config:
        json_schema_extra = {
            "example": {
                "tour_program_code": "NNSGN87"
            }
        }


class TourAvailableDate(BaseModel):
    """Check available dates for a specific tour program."""

    tour_program_code: Annotated[str, "Unique identifier code for the tour program"]

    class Config:
        json_schema_extra = {
            "example": {
                "tour_program_code": "NNSGN87"
            }
        }


class BookTour(BaseModel):
    """Book a tour based on the provided details."""

    tour_code: Annotated[str, "The unique identifier for the tour to book"]
    customer_name: Annotated[Optional[str], "The name of the customer booking the tour"]
    customer_phone: Annotated[Optional[str], "The phone number of the customer booking the tour"]
    customer_email: Annotated[Optional[str], "The email address of the customer booking the tour"]
    customer_address: Annotated[Optional[str], "The address of the customer booking the tour"] = None
    from_date: Annotated[Optional[str], "The starting date of the tour in 'yyyy-mm-dd' format"]
    num_of_adult: Annotated[Optional[int], "Number of adult passengers"]
    num_of_child: Annotated[Optional[int], "Number of child passengers"]

    class Config:
        json_schema_extra = {
            "example": {
                "tour_code": "NNSGN87-004-290525CX-P"
            }
        }


class CancelTour(BaseModel):
    """Cancel an existing tour booking by its booking ID."""

    booking_id: Annotated[str, "The unique identifier for the booking to cancel"]

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "bk123456"
            }
        }
