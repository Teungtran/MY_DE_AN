from ...appointment_graph.tools.get_sql import connect_to_db
from config.base_config import APP_CONFIG
from ...appointment_graph.tools.get_id import generate_short_id
sql_config = APP_CONFIG.sql_config
from sqlalchemy import text
from datetime import datetime
db = connect_to_db(server=sql_config.server, database=sql_config.database)
from langchain_core.tools import tool
from typing import  Optional
from schemas.device_schemas import TrackTicket,CancelTicket,SendTicket
@tool("send_ticket",args_schema=SendTicket)
def send_ticket(
    content: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Tool to send a ticket to report a problem.
    """
    try:
        # Generate booking_id first
        ticket_id = f"TICKET_{generate_short_id()}"
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Prepare parameters
        params = {
            "ticket_id": ticket_id,
            "content": content,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "description": description,
            "status": "Pending"
        }

        # Prepare SQL query
        insert_query = text("""
            INSERT INTO ticket (
                ticket_id, content, customer_name, customer_phone, time, description, status
            ) VALUES (
                :ticket_id, :content, :customer_name, :customer_phone, :time, :description, :status
            )
        """)

        with db._engine.connect() as conn:
            conn.execute(insert_query, params)
            conn.commit()
            
        return {
            "ticket_id": ticket_id,
            "content": content,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "description": description,
            "status": "Pending",
            "message": f"Ticket {ticket_id} for {content} has been successfully sent, please wait for IT support."
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in book_appointment: {str(e)}")
        return {"error": f"Error booking appointment: {str(e)}"}
@tool("track_ticket",args_schema=TrackTicket)
def track_ticket(ticket_id: str) -> list[dict]:
    """
    Tool to track ticket info and status by ticket_id
    """
    try:
        track_query = text("""
            SELECT *
            FROM ticket
            WHERE ticket_id = :ticket_id
        """)
        with db._engine.connect() as conn:
            result = conn.execute(track_query, {"ticket_id": ticket_id}).fetchone()

        if not result:
            return f"Ticket with ID {ticket_id} not found."


        return result

    except Exception as e:
        return f"Error tracking order: {str(e)}"
@tool("cancel_ticket",args_schema=CancelTicket)
def cancel_ticket(
    ticket_id: str,
) -> str:
    """
    Tool to cancel ticket by ticket_id
    """
    try:
        check_query = text("SELECT status FROM ticket WHERE ticket_id = :ticket_id")
        with db._engine.connect() as conn:
            result = conn.execute(check_query, {"ticket_id": ticket_id}).fetchone()

        if not result:
            return f"Ticket with ID {ticket_id} not found."

        if result[0] in ["Canceled"]:
            return f"Cannot cancel Ticket. Current status: {result[0]}"

        update_query = text("UPDATE Booking SET status = 'Canceled' WHERE booking_id = :booking_id")
        with db._engine.connect() as conn:
            conn.execute(update_query, {"ticket_id": ticket_id})
            conn.commit()

        return f"Ticket {ticket_id} cancelled successfully."

    except Exception as e:
        return f"Error cancelling Ticket: {str(e)}"