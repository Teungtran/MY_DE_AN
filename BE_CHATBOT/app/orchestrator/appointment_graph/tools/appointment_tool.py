from langchain_core.tools import tool
from typing import Optional
from schemas.device_schemas import BookAppointment, TrackAppointment, CancelAppointment, UpdateAppointment
from config.base_config import APP_CONFIG
from .get_id import generate_short_id
from utils.email import send_email
from pydantic import EmailStr
from models.database import Booking, SessionLocal

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
            email_subject = "Your FPT Shop Appointment Confirmation"
            email_body = f"""
            Dear {customer_name},

            Thank you for scheduling an appointment with FPT Shop!

            We're pleased to confirm your appointment with the following details:

            🗓️ Appointment Details
            - Booking ID: {booking_id}
            - Reason: {reason}
            - Date and Time: {time}
            - Note: {note or "No additional notes"}

            Please save your booking ID for future reference. You can use it to track, update, or cancel your appointment if needed.

            For any questions or concerns, please contact our customer support team:

            Sales Consultation (Free of Charge)  
            📞 1800.6601 (Press 1)

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            We look forward to seeing you!

            Best regards,  
            FPT Shop Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {customer_name},

            Cảm ơn bạn đã đặt lịch hẹn tại FPT Shop!

            Chúng tôi xin xác nhận lịch hẹn của bạn với các thông tin sau:

            🗓️ Chi tiết lịch hẹn
            - Mã đặt lịch: {booking_id}
            - Lý do: {reason}
            - Ngày và giờ: {time}
            - Ghi chú: {note or "Không có ghi chú bổ sung"}

            Vui lòng lưu mã đặt lịch để tham khảo trong tương lai. Bạn có thể sử dụng mã này để theo dõi, cập nhật hoặc hủy lịch hẹn nếu cần.

            Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào, vui lòng liên hệ bộ phận chăm sóc khách hàng của chúng tôi:

            Tư vấn mua hàng (Miễn phí)  
            📞 1800.6601 (Nhánh 1)

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Chúng tôi rất mong được gặp bạn!

            Trân trọng,  
            Đội ngũ FPT Shop  
            https://fptshop.com.vn
            """
            
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
            
        # Return booking confirmation with message
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

        # Send email notification if email is provided
        if email:
            email_subject = "Your FPT Shop Appointment Has Been Updated"
            email_body = f"""
            Dear {updated["customer_name"]},

            Your appointment with FPT Shop has been successfully updated. Please review the updated details below:

            🗓️ Updated Appointment Details
            - Booking ID: {booking_id}
            - Reason: {updated["reason"]}
            - Date and Time: {updated["time"]}
            - Note: {updated["note"] or "No additional notes"}

            For any questions or concerns, please contact our customer support team:

            Sales Consultation (Free of Charge)  
            📞 1800.6601 (Press 1)

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            We look forward to seeing you!

            Best regards,  
            FPT Shop Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {updated["customer_name"]},

            Lịch hẹn của bạn với FPT Shop đã được cập nhật thành công. Vui lòng xem lại thông tin cập nhật dưới đây:

            🗓️ Chi tiết lịch hẹn đã cập nhật
            - Mã đặt lịch: {booking_id}
            - Lý do: {updated["reason"]}
            - Ngày và giờ: {updated["time"]}
            - Ghi chú: {updated["note"] or "Không có ghi chú bổ sung"}

            Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào, vui lòng liên hệ bộ phận chăm sóc khách hàng của chúng tôi:

            Tư vấn mua hàng (Miễn phí)  
            📞 1800.6601 (Nhánh 1)

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Chúng tôi rất mong được gặp bạn!

            Trân trọng,  
            Đội ngũ FPT Shop  
            https://fptshop.com.vn
            """
            
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
    Tool to track order info and status by order id
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
        return f"Error tracking order: {str(e)}"

@tool("cancel_appointment", args_schema=CancelAppointment)
def cancel_appointment(
    booking_id: str,
    email: EmailStr = None
) -> str:
    """
    Tool to cancel order by order id
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
            
        # Send email notification if email is provided
        if email:
            email_subject = "Your FPT Shop Appointment Has Been Canceled"
            email_body = f"""
            Dear {customer_name},

            Your appointment with booking ID {booking_id} has been successfully canceled.

            If you wish to schedule a new appointment, please ask SAGE to help you or contact our customer support:

            📞 Customer Support (Free Call): 1800.6601 (Call Center 1)
            
            Thank you for choosing FPT Shop.

            Best regards,  
            FPT Shop Team  
            https://fptshop.com.vn

            ---------------------------VIETNAMESE VERSION BELOW ---------------------------

            Kính gửi {customer_name},

            Lịch hẹn của bạn với mã đặt lịch {booking_id} đã được hủy thành công.

            Nếu bạn muốn đặt lịch hẹn mới, vui lòng sử dụng SAGE hoặc liên hệ với bộ phận hỗ trợ khách hàng:

            📞 Hỗ trợ khách hàng (Miễn phí): 1800.6601 (Tổng đài 1)
            
            Cảm ơn bạn đã lựa chọn FPT Shop.

            Trân trọng,  
            Đội ngũ FPT Shop  
            https://fptshop.com.vn
            """
            
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return f"Appointment {booking_id} cancelled successfully. Cancellation confirmation has been sent to your email."

    except Exception as e:
        return f"Error cancelling Appointment: {str(e)}"
