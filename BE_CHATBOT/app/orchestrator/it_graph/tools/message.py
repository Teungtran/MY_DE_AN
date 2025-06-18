from ...appointment_graph.tools.get_sql import connect_to_db
from config.base_config import APP_CONFIG
from ...appointment_graph.tools.get_id import generate_short_id
from sqlalchemy import text
from datetime import datetime
from langchain_core.tools import tool
from typing import Optional
from schemas.device_schemas import TrackTicket, CancelTicket, SendTicket, UpdateTicket
from utils.email import send_email
from pydantic import EmailStr
from sqlalchemy.orm import Session
from models.database import Ticket, get_db, SessionLocal

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
        time_now = datetime.now()
        
        # Create a new Ticket object
        new_ticket = Ticket(
            ticket_id=ticket_id,
            content=content,
            customer_name=customer_name,
            customer_phone=customer_phone,
            time=time_now,
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
            email_subject = "Your FPT Shop IT Support Ticket Confirmation"
            email_body = f"""
            Dear {customer_name},

            Thank you for submitting an IT support ticket with FPT Shop!

            We're pleased to confirm your ticket has been received with the following details:

            🎫 Ticket Details
            - Ticket ID: {ticket_id}
            - Description: {description or "No description provided"}
            - Content: {content}
            - Time Submitted: {time_now}
            - Status: Pending

            Please save your ticket ID for future reference. You can use it to track, update, or cancel your ticket if needed.

            Our IT support team will review your ticket and respond as soon as possible. For urgent matters, please contact our technical support directly:

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            Thank you for your patience!

            Best regards,  
            FPT Shop IT Support Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {customer_name},

            Cảm ơn bạn đã gửi yêu cầu hỗ trợ IT tại FPT Shop!

            Chúng tôi xin xác nhận yêu cầu của bạn đã được tiếp nhận với các thông tin sau:

            🎫 Chi tiết yêu cầu
            - Mã yêu cầu: {ticket_id}
            - Mô tả: {description or "Không có mô tả"}
            - Nội dung: {content}
            - Thời gian gửi: {time_now}
            - Trạng thái: Đang chờ xử lý

            Vui lòng lưu mã yêu cầu để tham khảo trong tương lai. Bạn có thể sử dụng mã này để theo dõi, cập nhật hoặc hủy yêu cầu nếu cần.

            Đội ngũ hỗ trợ IT của chúng tôi sẽ xem xét yêu cầu của bạn và phản hồi trong thời gian sớm nhất. Đối với các vấn đề khẩn cấp, vui lòng liên hệ trực tiếp với bộ phận hỗ trợ kỹ thuật:

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Cảm ơn sự kiên nhẫn của bạn!

            Trân trọng,  
            Đội ngũ Hỗ trợ IT FPT Shop  
            https://fptshop.com.vn
            """
            
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
            "time": time_now,
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
            email_subject = "Your FPT Shop IT Support Ticket Has Been Updated"
            email_body = f"""
            Dear {updated["customer_name"]},

            Your IT support ticket with FPT Shop has been successfully updated. Please review the updated details below:

            🎫 Updated Ticket Details
            - Ticket ID: {ticket_id}
            - Description: {updated["description"] or "No description provided"}
            - Content: {updated["content"]}
            - Time Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            Our IT support team will continue to work on your ticket with the updated information. For urgent matters, please contact our technical support directly:

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            Thank you for your patience!

            Best regards,  
            FPT Shop IT Support Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {updated["customer_name"]},

            Yêu cầu hỗ trợ IT của bạn với FPT Shop đã được cập nhật thành công. Vui lòng xem lại thông tin cập nhật dưới đây:

            🎫 Chi tiết yêu cầu đã cập nhật
            - Mã yêu cầu: {ticket_id}
            - Mô tả: {updated["description"] or "Không có mô tả"}
            - Nội dung: {updated["content"]}
            - Thời gian cập nhật: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            Đội ngũ hỗ trợ IT của chúng tôi sẽ tiếp tục xử lý yêu cầu của bạn với thông tin đã cập nhật. Đối với các vấn đề khẩn cấp, vui lòng liên hệ trực tiếp với bộ phận hỗ trợ kỹ thuật:

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Cảm ơn sự kiên nhẫn của bạn!

            Trân trọng,  
            Đội ngũ Hỗ trợ IT FPT Shop  
            https://fptshop.com.vn
            """
            
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
            email_subject = "Your FPT Shop IT Support Ticket Has Been Canceled"
            email_body = f"""
            Dear {customer_name},

            Your IT support ticket with ID {ticket_id} has been successfully canceled.

            If you need further assistance, please submit a new ticket or contact our technical support directly:

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)
            
            Thank you for choosing FPT Shop.

            Best regards,  
            FPT Shop IT Support Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {customer_name},

            Yêu cầu hỗ trợ IT của bạn với mã số {ticket_id} đã được hủy thành công.

            Nếu bạn cần hỗ trợ thêm, vui lòng gửi yêu cầu mới hoặc liên hệ trực tiếp với bộ phận hỗ trợ kỹ thuật:

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)
            
            Cảm ơn bạn đã lựa chọn FPT Shop.

            Trân trọng,  
            Đội ngũ Hỗ trợ IT FPT Shop  
            https://fptshop.com.vn
            """
            
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return f"Ticket {ticket_id} cancelled successfully. Cancellation confirmation has been sent to your email."

    except Exception as e:
        return f"Error cancelling ticket: {str(e)}"