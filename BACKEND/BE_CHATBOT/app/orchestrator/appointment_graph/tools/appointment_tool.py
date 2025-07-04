from langchain_core.tools import tool
from typing import Optional
from schemas.device_schemas import BookAppointment, TrackAppointment, CancelAppointment, UpdateAppointment
from config.base_config import APP_CONFIG
from .get_id import generate_short_id
from utils.email import send_email
from pydantic import EmailStr
from models.database import Booking, SessionLocal
from .send_email import send_appointment_cancel,send_appointment_confirmation,send_appointment_update
sql_config = APP_CONFIG.sql_config

# Create a function to get a database session
def get_appointment_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@tool("book_appointment", args_schema=BookAppointment)
def book_appointment(
    reason: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    time: str = None,  
    note: Optional[str] = None,
    user_id: str = None,
    email: EmailStr = None
) -> list[dict]:
    """
    Tool to book an appointment for the customer.
    """
    try:
        booking_id = f"BOOKING_{generate_short_id()}"
        
        # Create a new Booking object
        new_booking = Booking(
            booking_id=booking_id,
            reason=reason,
            customer_name=customer_name,
            customer_phone=customer_phone,
            time=time,
            note=note,
            status="Scheduled",
            user_id=user_id
        )
        
        # Get a database session
        db = get_appointment_db()
        
        try:
            # Add the booking to the database
            db.add(new_booking)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        # Send email confirmation if email is provided
        if email:
            email_subject, email_body = send_appointment_confirmation(customer_name, booking_id, reason, note, time)
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
            
        return {
            "booking_id": booking_id,
            "reason": reason,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "note": note,
            "status": "Scheduled",
            "message": f"Appointment {booking_id} for {reason} has been successfully scheduled. Please check your email for confirmation details."
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in book_appointment: {str(e)}")
        return {"error": f"Error booking appointment: {str(e)}"}
    
@tool("update_appointment", args_schema=UpdateAppointment)
def update_appointment(
    booking_id: str,
    reason: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    time: Optional[str] = None,
    user_id: str = None,
    email: EmailStr = None
) -> dict:
    """
    Tool to update an existing appointment. Only `booking_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        # Get a database session
        db = get_appointment_db()
        
        try:
            # Find the existing appointment
            existing_appointment = db.query(Booking).filter(Booking.booking_id == booking_id).first()
            
            if not existing_appointment:
                return {"error": f"Appointment '{booking_id}' not found."}
            
            # Update fields if provided
            if reason:
                existing_appointment.reason = reason
            if customer_name:
                existing_appointment.customer_name = customer_name
            if customer_phone:
                existing_appointment.customer_phone = customer_phone
            if note:
                existing_appointment.note = note
            if time:
                existing_appointment.time = time
            if user_id:
                existing_appointment.user_id = user_id
                
            # Commit the changes
            db.commit()
            
            # Get updated values for the response
            updated = {
                "reason": existing_appointment.reason,
                "customer_name": existing_appointment.customer_name,
                "customer_phone": existing_appointment.customer_phone,
                "note": existing_appointment.note,
                "time": existing_appointment.time,
                "booking_id": booking_id
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        if email:
            email_subject, email_body = send_appointment_update(updated, booking_id)
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return {
            "booking_id": booking_id,
            "reason": updated["reason"],
            "customer_name": updated["customer_name"],
            "customer_phone": updated["customer_phone"],
            "note": updated["note"],
            "time": updated["time"],
            "message": f"Appointment {booking_id} has been successfully updated. Please check your email for the updated details."
        }

    except Exception as e:
        print(f"Error in update_appointment: {str(e)}")
        return {"error": f"Error updating Appointment: {str(e)}"}

@tool("track_appointment", args_schema=TrackAppointment)
def track_appointment(booking_id: str) -> list[dict]:
    """
    Tool to track appointment info and status by appointment id
    """
    try:
        # Get a database session
        db = get_appointment_db()
        
        try:
            # Find the appointment
            appointment = db.query(Booking).filter(Booking.booking_id == booking_id).first()
            
            if not appointment:
                return f"Appointment with ID {booking_id} not found."
                
            # Convert to dictionary for response
            result = {
                "booking_id": appointment.booking_id,
                "reason": appointment.reason,
                "customer_name": appointment.customer_name,
                "customer_phone": appointment.customer_phone,
                "time": appointment.time,
                "note": appointment.note,
                "status": appointment.status,
                "user_id": appointment.user_id
            }
        finally:
            db.close()

        return result

    except Exception as e:
        return f"Error tracking appointment: {str(e)}"

@tool("cancel_appointment", args_schema=CancelAppointment)
def cancel_appointment(
    booking_id: str,
    email: EmailStr = None
) -> str:
    """
    Tool to cancel appointment by appointment id
    """
    try:
        # Get a database session
        db = get_appointment_db()
        
        try:
            # Find the appointment
            appointment = db.query(Booking).filter(Booking.booking_id == booking_id).first()
            
            if not appointment:
                return f"Appointment with ID {booking_id} not found."
                
            if appointment.status in ["Finished", "Canceled"]:
                return f"Cannot cancel appointment. Current status: {appointment.status}"
                
            customer_name = appointment.customer_name
            
            # Update the status
            appointment.status = "Canceled"
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        if email:
            email_subject, email_body = send_appointment_cancel(booking_id,customer_name)
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return f"Appointment {booking_id} cancelled successfully. Cancellation confirmation has been sent to your email."

    except Exception as e:
        return f"Error cancelling Appointment: {str(e)}"
