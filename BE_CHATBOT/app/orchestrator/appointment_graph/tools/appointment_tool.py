from langchain_core.tools import tool
from typing import  Optional
from schemas.device_schemas import BookAppointment,TrackAppointment,CancelAppointment,UpdateAppointment
from config.base_config import APP_CONFIG
from sqlalchemy import text
from .get_sql import connect_to_db
from .get_id import generate_short_id
sql_config = APP_CONFIG.sql_config

db = connect_to_db(server="DESKTOP-LU731VP\\SQLEXPRESS", database="CUSTOMER_SERVICE")

@tool("book_appointment",args_schema=BookAppointment)
def book_appointment(
    reason: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    time: str = None,  
    note: Optional[str] = None,
    user_id: str = None
) -> list[dict]:
    """
    Tool to book an appointment for the customer.
    """
    try:

        booking_id = f"BOOKING_{generate_short_id()}"
        
        # Prepare parameters
        params = {
            "booking_id": booking_id,
            "reason": reason,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "note": note,
            "status": "Scheduled",
            "user_id": user_id
        }

        # Prepare SQL query
        insert_query = text("""
            INSERT INTO Booking (
                booking_id, reason, customer_name, customer_phone, time, note, status, user_id
            ) VALUES (
                :booking_id, :reason, :customer_name, :customer_phone, :time, :note, :status,:user_id
            )
        """)

        # Execute the query within a proper context manager
        with db._engine.connect() as conn:
            conn.execute(insert_query, params)
            conn.commit()
            
        # Return booking confirmation with message
        return {
            "booking_id": booking_id,
            "reason": reason,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "note": note,
            "status": "Scheduled",
            "message": f"Appointment {booking_id} for {reason} has been successfully scheduled."
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in book_appointment: {str(e)}")
        return {"error": f"Error booking appointment: {str(e)}"}
    
@tool("update_appointment", args_schema=UpdateAppointment)
def update_appointment(
    booking_id: str,
    reason: Optional[str] = None,
    customer_name:  Optional[str] = None,
    customer_phone:  Optional[str] = None,
    note:  Optional[str] = None,
    time:  Optional[str] = None,
    user_id:  str = None
) -> dict:
    """
    Tool to update an existing appointment. Only `booking_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        with db._engine.connect() as conn:
            select_query = text("SELECT * FROM Booking WHERE booking_id = :booking_id")
            existing_appointment = conn.execute(select_query, {"booking_id": booking_id}).fetchone()

            if not existing_appointment:
                return {"error": f"Appointment '{booking_id}' not found."}

            columns = existing_appointment._fields
            appointment_data = dict(zip(columns, existing_appointment))

            updated = {
                "reason": reason or appointment_data["reason"],
                "customer_name": customer_name or appointment_data["customer_name"],
                "customer_phone": customer_phone or appointment_data["customer_phone"],
                "note": note or appointment_data["note"],
                "time": time or appointment_data["time"],
                "booking_id": booking_id,
                "user_id": user_id
            }

            update_query = text("""
                UPDATE Booking
                SET
                    reason = :reason,
                    customer_name = :customer_name,
                    customer_phone = :customer_phone,
                    note = :note,
                    time = :time
                WHERE booking_id = :booking_id
            """)
            conn.execute(update_query, updated)
            conn.commit()


        return {
            "booking_id": booking_id,
            "reason": updated["reason"],
            "customer_name": updated["customer_name"],
            "customer_phone": updated["customer_phone"],
            "note": updated["note"],
            "time": updated["time"],
            "message": f"Appointment {booking_id} has been successfully updated."
        }

    except Exception as e:
        print(f"Error in update_appointment: {str(e)}")
        return {"error": f"Error updating Appointment: {str(e)}"}
@tool("track_appointment",args_schema=TrackAppointment)
def track_appointment(booking_id: str) -> list[dict]:
    """
    Tool to track order info and status by order id
    """
    try:
        track_query = text("""
            SELECT *
            FROM Booking
            WHERE booking_id = :booking_id
        """)
        with db._engine.connect() as conn:
            result = conn.execute(track_query, {"booking_id": booking_id}).fetchone()

        if not result:
            return f"Appointment with ID {booking_id} not found."


        return result

    except Exception as e:
        return f"Error tracking order: {str(e)}"
@tool("cancel_appointment",args_schema=CancelAppointment)
def cancel_appointment(
    booking_id: str,
) -> str:
    """
    Tool to cancel order by order id
    """
    try:
        check_query = text("SELECT status FROM Booking WHERE booking_id = :booking_id")
        with db._engine.connect() as conn:
            result = conn.execute(check_query, {"booking_id": booking_id}).fetchone()

        if not result:
            return f"Appointment with ID {booking_id} not found."

        if result[0] in ["Finished", "Canceled",]:
            return f"Cannot cancel appointment. Current status: {result[0]}"

        update_query = text("UPDATE Booking SET status = 'Canceled' WHERE booking_id = :booking_id")
        with db._engine.connect() as conn:
            conn.execute(update_query, {"booking_id": booking_id})
            conn.commit()

        return f"Appointment {booking_id} cancelled successfully."

    except Exception as e:
        return f"Error cancelling Appointment: {str(e)}"
