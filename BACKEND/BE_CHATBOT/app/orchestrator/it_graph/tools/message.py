from config.base_config import APP_CONFIG
from ...appointment_graph.tools.get_id import generate_short_id
from datetime import datetime
from langchain_core.tools import tool
from typing import Optional
from schemas.device_schemas import TrackTicket, CancelTicket, SendTicket, UpdateTicket
from utils.email import send_email
from pydantic import EmailStr
from models.database import Ticket, SessionLocal
from .send_email import send_ticket_cancel,send_ticket_confirmation,send_ticket_update
sql_config = APP_CONFIG.sql_config

# Create a function to get a database session
def get_ticket_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@tool("send_ticket", args_schema=SendTicket)
def send_ticket(
    content: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    description: Optional[str] = None,
    user_id: str = None,
    email: EmailStr = None
) -> dict:
    """
    Tool to send a ticket to report a problem.
    """
    try:
        # Generate ticket_id
        ticket_id = f"TICKET_{generate_short_id()}"
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a new Ticket object
        new_ticket = Ticket(
            ticket_id=ticket_id,
            content=content,
            customer_name=customer_name,
            customer_phone=customer_phone,
            time=time,
            description=description,
            status="Pending",
            user_id=user_id
        )
        
        # Get a database session
        db = get_ticket_db()
        
        try:
            # Add the ticket to the database
            db.add(new_ticket)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        # Send email confirmation if email is provided
        if email:
            email_subject, email_body = send_ticket_confirmation(customer_name, ticket_id, description, content, time)
            
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
            
        return {
            "ticket_id": ticket_id,
            "content": content,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "time": time,
            "description": description,
            "status": "Pending",
            "message": f"Ticket {ticket_id} for {content} has been successfully sent, please wait for IT support. Please check your email for confirmation details."
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in send_ticket: {str(e)}")
        return {"error": f"Error sending ticket: {str(e)}"}

@tool("update_ticket", args_schema=UpdateTicket)
def update_ticket(
    ticket_id: str,
    content: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    description: Optional[str] = None,
    time: Optional[str] = None,
    user_id: str = None,
    email: EmailStr = None
) -> dict:
    """
    Tool to update an existing ticket. Only `ticket_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        # Get a database session
        db = get_ticket_db()
        
        try:
            # Find the existing ticket
            existing_ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            
            if not existing_ticket:
                return {"error": f"Ticket '{ticket_id}' not found."}
            
            # Update fields if provided
            if content:
                existing_ticket.content = content
            if customer_name:
                existing_ticket.customer_name = customer_name
            if customer_phone:
                existing_ticket.customer_phone = customer_phone
            if description:
                existing_ticket.description = description
            if time:
                existing_ticket.time = time
            if user_id:
                existing_ticket.user_id = user_id
                
            # Commit the changes
            db.commit()
            
            # Get updated values for the response
            updated = {
                "content": existing_ticket.content,
                "customer_name": existing_ticket.customer_name,
                "customer_phone": existing_ticket.customer_phone,
                "description": existing_ticket.description,
                "time": existing_ticket.time,
                "ticket_id": ticket_id
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        # Send email notification if email is provided
        if email:
            email_subject, email_body = send_ticket_update(updated,ticket_id)
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return {
            "ticket_id": ticket_id,
            "content": updated["content"],
            "customer_name": updated["customer_name"],
            "customer_phone": updated["customer_phone"],
            "description": updated["description"],
            "time": updated["time"],
            "message": f"Ticket {ticket_id} has been successfully updated. Please check your email for the updated details."
        }

    except Exception as e:
        print(f"Error in update_ticket: {str(e)}")
        return {"error": f"Error update_ticket: {str(e)}"}

@tool("track_ticket", args_schema=TrackTicket)
def track_ticket(ticket_id: str) -> list[dict]:
    """
    Tool to track ticket info and status by ticket_id
    """
    try:
        # Get a database session
        db = get_ticket_db()
        
        try:
            # Find the ticket
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            
            if not ticket:
                return f"Ticket with ID {ticket_id} not found."
                
            # Convert to dictionary for response
            result = {
                "ticket_id": ticket.ticket_id,
                "content": ticket.content,
                "customer_name": ticket.customer_name,
                "customer_phone": ticket.customer_phone,
                "time": ticket.time,
                "description": ticket.description,
                "status": ticket.status,
                "user_id": ticket.user_id
            }
        finally:
            db.close()

        return result

    except Exception as e:
        return f"Error tracking ticket: {str(e)}"

@tool("cancel_ticket", args_schema=CancelTicket)
def cancel_ticket(
    ticket_id: str,
    email: EmailStr = None
) -> str:
    """
    Tool to cancel ticket by ticket_id
    """
    try:
        # Get a database session
        db = get_ticket_db()
        
        try:
            # Find the ticket
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            
            if not ticket:
                return f"Ticket with ID {ticket_id} not found."
                
            if ticket.status in ["Canceled"]:
                return f"Cannot cancel ticket. Current status: {ticket.status}"
                
            customer_name = ticket.customer_name
            
            # Update the status
            ticket.status = "Canceled"
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        # Send email notification if email is provided
        if email:
            email_subject, email_body = send_ticket_cancel(ticket_id,customer_name)
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return f"Ticket {ticket_id} cancelled successfully. Cancellation confirmation has been sent to your email."

    except Exception as e:
        return f"Error cancelling ticket: {str(e)}"