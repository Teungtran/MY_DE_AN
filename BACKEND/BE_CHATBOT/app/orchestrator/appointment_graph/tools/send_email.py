def send_appointment_confirmation(customer_name, booking_id, reason, note,time):
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

    return email_subject, email_body

from typing_extensions import Dict

def send_appointment_update(updated: Dict, booking_id):
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
    return email_subject, email_body



def send_appointment_cancel(booking_id,customer_name):
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
    return email_subject, email_body