import asyncio
from agno.tools import tool
from .support.crawler import URLCrawler
from .support.get_point import get_all_points
from .support.get_similarity import calculate_similarities_batch
from .support.get_type import get_type

@tool(
    name="extract_url_content", 
    description="Extract content from URL (https://),if user ask to generate an ad script from URL",
    instructions="Get and extract content from URL (https://) if user ask to generate an ad script from URL",
    add_instructions=True, 
    cache_results=True)
def extract_url_content(url: str) -> str:
    """Extract content from URL and format as advertisement context."""
    crawler = URLCrawler()
    
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Run the async function
        try:
            content_and_url = loop.run_until_complete(crawler.get_converted_document(url))
        except RuntimeError as e:
            # If loop is already running, we need to handle it differently
            if "already running" in str(e).lower():
                # Create a new loop for this specific call
                new_loop = asyncio.new_event_loop()
                content_and_url = new_loop.run_until_complete(crawler.get_converted_document(url))
                new_loop.close()
            else:
                raise
        
        if content_and_url:
            content, final_url = content_and_url
            ad = (
                f"**Advertisement context:{content.strip()}**\n\n"
                f"[Buy Now]({final_url})"
            )
            return ad
        else:
            return "Failed to extract content from the URL."
            
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = traceback.format_exc()
        return f"Error extracting content from URL '{url}': {str(e)}\nDetails: {error_details[:200]}"
    
    
@tool(name="draft_advertise_from_input", 
    description="Tool to write a Commercial Ad for all devices such as phone ,laptop/pc, earphone, mouse, keyboard",
    instructions="get user input if they request to draft an ad script support for all devices such as phone ,laptop/pc, earphone, mouse, keyboard",
    add_instructions=True,
    cache_results=True)
def draft_advertise_from_input(user_input:str) -> str:
    inferred = get_type.run(user_input)
    # Handle case where response_model parsing fails and content is a string
    if isinstance(inferred.content, str):
        device_type = "get_all"
    else:
        # Check if content has type attribute (InferredDeviceType object)
        device_type = getattr(inferred.content, 'type', None) or "get_all"
    
    points_by_type = get_all_points(type=device_type)
    points = points_by_type.get(device_type, [])

    if not points:
        return f"No products found for type '{device_type}'."

    similarities = calculate_similarities_batch(user_input.lower(), points, field="device_name")

    if not similarities:
        return "No good match found for your query."

    top_idx = max(similarities, key=similarities.get)
    top_score = similarities[top_idx]
    best_match = points[top_idx]

    if top_score < 0.1:
        return "No good match found for your query."

    def format_number(value, default="N/A"):
        """Format number with commas or return default."""
        try:
            return f"{int(value):,}" if value else default
        except (ValueError, TypeError):
            return str(value) if value else default
    
    metadata = best_match.payload.get("metadata", {})
    device_name = metadata.get("device_name", "Unnamed Device")
    description = best_match.payload.get("page_content", "No description available.")
    price = format_number(metadata.get("sale_price"), "Contact for price")
    discount_percent = metadata.get("discount_percent", 0)
    installment_price = format_number(metadata.get("installment_price"), "N/A")
    source = metadata.get("source", "https://www.example.com")
    color = ", ".join(metadata.get("colors", [])) or "Various colors"
    sales_perks = metadata.get("sales_perks", "")
    guarantee = metadata.get("guarantee_program", "")
    payment_perks = metadata.get("payment_perks", "")

    ad = (
        f"**🔥 {device_name} — Now on Sale!**\n\n"
        f"{description.strip()}\n\n"
        f"Price: **{price} VND** — that's a **{discount_percent}% discount**!\n"
        f"Installment: **{installment_price} VND/month**\n"
        f"Perks:\n- {sales_perks}\n- {payment_perks}\n- {guarantee}\n"
        f"Color: {color}\n\n"
        f"[Buy Now]({source})"
    )
    return ad
