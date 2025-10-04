from datetime import datetime

def send_ticket_confirmation(customer_name, ticket_id, description, content, time):
    email_subject = "Your FPT Shop IT Support Ticket Confirmation"
    email_body = f"""
    Dear {customer_name},

    Thank you for submitting an IT support ticket with FPT Shop!

    We're pleased to confirm your ticket has been received with the following details:

    🎫 Ticket Details
    - Ticket ID: {ticket_id}
    - Description: {description or "No description provided"}
    - Content: {content}
    - Time Submitted: {time}
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
    - Thời gian gửi: {time}
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
    return email_subject, email_body


from typing_extensions import Dict

def send_ticket_update(updated: Dict, ticket_id):
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
    
    return email_subject, email_body



def send_ticket_cancel(ticket_id,customer_name):
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
    
    return email_subject, email_body