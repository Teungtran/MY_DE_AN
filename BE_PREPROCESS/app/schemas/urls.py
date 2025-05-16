from typing import Dict, List, Optional,Literal, Annotated

from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict
from typing import Annotated, List,Literal
from schemas.document_metadata import DocumentMetadata

class UrlsRequest(BaseModel):
    urls: List[DocumentMetadata]


class UrlsResponse(BaseModel):
    """Response body after accepting URLs for processing."""

    message: str


class WebhookRequest(BaseModel):
    """Payload sent TO the webhook URL."""

    succeeded_urls: List[str] = Field(..., description="List of successfully processed URLs")
    failed_urls: List[str] = Field(..., description="List of URLs that failed processing (crawler returned None)")
    error_urls: List[Dict[str, str]] = Field(
        ...,
        description="List of URLs with errors during processing, including the error message [{'url': url, 'error': msg}]",
    )
    message: str = Field(..., description="Status of the S3 upload ('succeeded', 'failed')")
    trace_id: str


class WebhookResponse(BaseModel):
    """Response expected FROM the webhook endpoint (if you implement one)."""

    message: str
    trace_id: Optional[str] = None


class FPTData(BaseModel):
    """Details of an electronic device including specifications, promotions, and warranty."""

    model_config = ConfigDict(extra='forbid')  

    device_name: Annotated[
        str,
        "Name of the electronic device. Example: 'iPhone 15'"
    ]

    storage: Annotated[
        List[str],
        "Storage capacitíe in GB. Example: ['256', '512']"
    ]
    battery: Annotated[
        str,
        "Information about batter ."
    ]
    cpu: Annotated[
        str,
        "CPU of the computer/laptop. Example: 'Ryzen 5'"
    ]
    card: Annotated[
        str,
        "graphic card of the laptop.Example: 'AMD Radeon Graphics'"
    ]
    screen: Annotated[
        str,
        "Information about screen.Example: '14 inch'"
    ]
    sale_price: Annotated[
        int,
        "Current discounted price in VND. Digits only, no symbols or separators. Example: 4990000"
    ]
    original_price: Annotated[
        Optional[int],
        "Original price before discount (if available). Digits only. Example: 6490000"
    ]
    discount_percent: Annotated[
        Optional[int],
        "Discount percentage without % symbol. Example: 23"
    ]
    installment_price: Annotated[
        Optional[int],
        "Monthly installment amount in VND, digits only. Example: 972750"
    ]
    bonus_points: Annotated[
        Optional[int],
        "Promotional bonus points awarded. Digits only. Example: 1247"
    ]
    suitable_for: Annotated[
        Optional[Literal[
            "students", "adults"
        ]],
        "what type of customer is suitable for this device based on sale_price. follow strictly this rule: if sale_price less than 1000000 then suitable_for is 'students' and if sale_price is more than 10000000 then suitable_for is 'adult'"
    ] = None
    
    colors: Annotated[
        List[str],
        "Available colors of the device. Example: ['black', 'blue']"
    ]

    sales_perks: Annotated[
        str,
        "All detailed text (TRY to find in \"Quà tặng và ưu đãi khác\" and under \"Khuyến mãi được hưởng\") regarding gifts, other sales perks, extra offers, interest-free installment plans. Include exact text from the website with full promotional wording."
    ]

    guarantee_program: Annotated[
        str,
        "ALL Warranty or guarantee program associated with the device. Look for sections like \"Bảo hành mở rộng\" containing information about extended warranties and care programs."
    ]
    
    payment_perks: Annotated[
        str,
        "All detailed text (Try to find in \"Khuyến mãi thanh toán\") regarding promotions, perks, bonus programs, installment options, and payment-related discounts. Include full promotional terms   "
    ]

    image_link: Annotated[
        str,
        "ALL URL links to the device's featured image in the ### IMAGE section"
    ]

    source: Annotated[
        str,
        "Source URL of the product page"
    ] = None

