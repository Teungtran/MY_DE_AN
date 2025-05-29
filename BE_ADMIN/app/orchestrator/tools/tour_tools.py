from factories.vector_store_factory import create_vector_store
from config.base_config import BaseConfiguration
from langchain_core.tools import tool
from schemas.tour_schemas import SearchTourProgram, TourProgramDetail, TourAvailableDate, BookTour, CancelTour
from qdrant_client import models


def get_qdrant_retriever():
    config = BaseConfiguration().model_copy(deep=True)
    config.vector_store_config.collection_name = "TOUR_ADIVCE"
    qdrant = create_vector_store(config)
    qdrant_retriever = qdrant.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 20,
            # "fetch_k": 30,
            # "lambda_mult": 0.5,
            "filter": None
        }
    )
    return qdrant_retriever


qdrant_retriever = get_qdrant_retriever()


@tool("search_tour_program_tool", args_schema=SearchTourProgram, return_direct=True)
def search_tour_program(
    query: str,
    departure: str = None,
    destination: str = None,
    from_date: str = None,
    tour_line: str = None,
    trans_type: str = None,
    tour_program_code: str = None,
    price_from: float = None,
    duration: str = None
) -> str:
    """Search for tours based on the query with optional filters."""
    filter_conditions = []

    if departure:
        # Try both MatchValue and MatchText
        filter_conditions.append(
            models.FieldCondition(
                key="metadata.departure",
                match=models.MatchText(text=departure)
            )
        )

    if destination:
        filter_conditions.append(
            models.FieldCondition(
                key="metadata.destination",
                match=models.MatchText(text=destination)
            )
        )

    # if departure_date:
    #     filter_conditions.append(
    #         models.FieldCondition(
    #             key="metadata.departure_date",
    #             match=models.MatchValue(value=departure_date)
    #         )
    #     )

    results = qdrant_retriever.invoke(query, filter=models.Filter(must=filter_conditions))
    keys = ["departure", "destination", "tour_line", "trans_type", "tour_program_code", "price_from", "duration", "image_link", "source", "departure_date"]
    # values = [{**{k: r.metadata.get(k) for k in keys}, **{"page_content": r.page_content}} for r in results]
    values = [{k: r.metadata.get(k) for k in keys} for r in results]

    if values:
        return values

    return "No tour program found. Recommend for another option."


@tool("tour_program_detail_tool", args_schema=TourProgramDetail, return_direct=True)
def tour_program_detail(
    query: str,
    tour_program_code: str
) -> str:

    results = qdrant_retriever.invoke(query, filter=models.Filter(must=[
        models.FieldCondition(
            key="metadata.tour_program_code",
            match=models.MatchText(text=tour_program_code)
        )
    ]))

    if results:
        return results

    return "No tour program found. Recommend for another option."


@tool("tour_available_date_tool", args_schema=TourAvailableDate, return_direct=True)
def tour_available_date(
    tour_program_code: str
) -> str:
    return "No available date for this tour program. Recommend for another tour program."


@tool("book_tour_tool", args_schema=BookTour, return_direct=True)
def book_tour(
    tour_code: str,
    customer_name: str = None,
    customer_phone: str = None,
    customer_email: str = None,
    customer_address: str = None,
    from_date: str = None,
    num_of_adult: int = 1,
    num_of_child: int = 0
) -> str:
    return "Book successfully."


@tool("cancel_tour_tool", args_schema=CancelTour, return_direct=True)
def cancel_tour(
    booking_id: str
) -> str:
    return "Cancel successfully."
