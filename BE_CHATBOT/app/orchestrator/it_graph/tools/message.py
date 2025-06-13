from ...appointment_graph.tools.get_sql import connect_to_db
from config.base_config import APP_CONFIG
from ...appointment_graph.tools.get_id import generate_short_id
from sqlalchemy import text
from datetime import datetime
from langchain_core.tools import tool
from typing import  Optional
from schemas.device_schemas import TrackTicket,CancelTicket,SendTicket,UpdateTicket

sql_config = APP_CONFIG.sql_config

db = connect_to_db(server=sql_config.server, database=sql_config.database)

@tool("send_ticket",args_schema=SendTicket)
def send_ticket(
    content: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    description: Optional[str] = None,
    user_id: str = None
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
            "status": "Pending",
            "user_id": user_id
        }

        # Prepare SQL query
        insert_query = text("""
            INSERT INTO ticket (
                ticket_id, content, customer_name, customer_phone, time, description, status, user_id
            ) VALUES (
                :ticket_id, :content, :customer_name, :customer_phone, :time, :description, :status, :user_id
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

@tool("update_ticket", args_schema=UpdateTicket)
def update_ticket(
    ticket_id: str,
    content: Optional[str] = None,
    customer_name:  Optional[str] = None,
    customer_phone:  Optional[str] = None,
    description:  Optional[str] = None,
    time:  Optional[str] = None,
    user_id:  str = None
) -> dict:
    """
    Tool to update an existing ticker. Only `ticket_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        with db._engine.connect() as conn:
            select_query = text("SELECT * FROM ticket WHERE ticket_id = :ticket_id")
            existing_ticket = conn.execute(select_query, {"ticket_id": ticket_id}).fetchone()

            if not existing_ticket:
                return {"error": f"ticket '{ticket_id}' not found."}

            columns = existing_ticket._fields
            ticket_data = dict(zip(columns, existing_ticket))

            updated = {
                "content": content or ticket_data["content"],
                "customer_name": customer_name or ticket_data["customer_name"],
                "customer_phone": customer_phone or ticket_data["customer_phone"],
                "description": description or ticket_data["description"],
                "time": time or ticket_data["time"],
                "ticket_id": ticket_id,
                "user_id": user_id
            }

            update_query = text("""
                UPDATE Booking
                SET
                    content = :content,
                    customer_name = :customer_name,
                    customer_phone = :customer_phone,
                    description = :description,
                    payment = :payment,
                    shipping = :shipping,
                    time = :time
                WHERE ticket_id = :ticket_id
            """)
            conn.execute(update_query, updated)
            conn.commit()


        return {
            "ticket_id": ticket_id,
            "content": updated["content"],
            "customer_name": updated["customer_name"],
            "customer_phone": updated["customer_phone"],
            "description": updated["description"],
            "time": updated["time"],
            "message": f"Ticket {ticket_id} has been successfully updated."
        }

    except Exception as e:
        print(f"Error in update_ticket: {str(e)}")
        return {"error": f"Error update_ticket: {str(e)}"}
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
            return f"Cannot cancel appointment. Current status: {result[0]}"

        update_query = text("UPDATE Booking SET status = 'Canceled' WHERE booking_id = :booking_id")
        with db._engine.connect() as conn:
            conn.execute(update_query, {"ticket_id": ticket_id})
            conn.commit()

        return f"Appointment {ticket_id} cancelled successfully."

    except Exception as e:
        return f"Error cancelling Appointment: {str(e)}"