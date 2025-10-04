def send_order_confirmation(customer_name, order_id, device_name, quantity_int, shipping, payment, address, customer_phone, time, order_price):
    email_subject = "Your FPT Shop Order Confirmation"
    email_body = f"""
                        Kính gửi {customer_name},

                        Cảm ơn bạn đã mua sắm tại FPT Shop!

                        Chúng tôi xin xác nhận đơn hàng {order_id} của bạn cho sản phẩm '{device_name}' đã được đặt thành công. Vui lòng xem lại thông tin đơn hàng dưới đây:

                        🛒 Thông tin đơn hàng
                        - Tên thiết bị: {device_name}
                        - Số lượng: {quantity_int}
                        - Ship tận nơi : {shipping}
                        - Phương thức thanh toán: {payment}
                        - Địa chỉ giao hàng: {address}
                        - Số điện thoại: {customer_phone}
                        - Trạng thái đơn hàng: Đang xử lý
                        - Thời gian nhận hàng: {time}

                        💳 Số tiền cần thanh toán: {order_price}

                        Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào, vui lòng liên hệ bộ phận chăm sóc khách hàng của chúng tôi qua:

                        Tư vấn mua hàng (Miễn phí)  
                        📞 1800.6601 (Nhánh 1)

                        Hỗ trợ kỹ thuật  
                        🛠️ 1800.6601 (Nhánh 2)

                        Góp ý, khiếu nại  
                        📢 1800.6616 (8:00 – 22:00)

                        Một lần nữa, xin cảm ơn bạn đã tin tưởng FPT Shop!

                        Trân trọng,  
                        Đội ngũ FPT Shop  
                        https://fptshop.com.vn
                        
                        ---------------------------ENGLISH VERSION BELOW ---------------------------
                        
                        Dear {customer_name},

                        Thank you for shopping with FPT Shop!

                        We're pleased to confirm that your order {order_id} for the device '{device_name}' has been successfully placed. Please review the order details below:

                        🛒 Order Details
                        - Device Name: {device_name}
                        - Quantity: {quantity_int}
                        - Shipping Method: {shipping}
                        - Payment Method: {payment}
                        - Shipping Address: {address}
                        - Phone Number: {customer_phone}
                        - Order Status: Processing
                        - Shipping Time: {time}

                        💳 Amount Due: {order_price}

                        For any questions or concerns, please don't hesitate to contact our customer support team through:

                        Sales Consultation (Free of Charge)  
                        📞 1800.6601 (Press 1)

                        Technical Support  
                        🛠️ 1800.6601 (Press 2)

                        Feedback & Complaints  
                        📢 1800.6616 (8:00 AM – 10:00 PM)

                        Thank you again for choosing FPT Shop!

                        Best regards,  
                        FPT Shop Team  
                        https://fptshop.com.vn
            """

    return email_subject, email_body
from typing_extensions import Dict

def send_order_update(updated: Dict, order_id):
    email_subject = "Your FPT Shop Order Update"
    email_body = f"""\
            Dear {updated["customer_name"]},

            Your order {order_id} has been successfully updated. Please review the latest order details below:

            🛒 Updated Order Details
            - Device Name: {updated["device_name"]}
            - Quantity: {updated["quantity"]}
            - Shipping Method: {updated["shipping"]}
            - Payment Method: {updated["payment"]}
            - Shipping Address: {updated["address"]}
            - Phone Number: {updated["customer_phone"]}
            - Reservation Time: {updated["time_reservation"]}

            💳 Updated Total: {updated["price"]}

            For any questions or concerns, please contact our customer support team:

            Sales Consultation (Free of Charge)  
            📞 1800.6601 (Press 1)

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            Thank you again for choosing FPT Shop!

            Best regards,  
            FPT Shop Team  
            https://fptshop.com.vn

            ---------------------------ENGLISH VERSION BELOW ---------------------------

            Kính gửi {updated["customer_name"]},

            Đơn hàng {order_id} của bạn đã được cập nhật thành công. Vui lòng kiểm tra thông tin mới nhất bên dưới:

            🛒 Thông tin đơn hàng cập nhật
            - Tên thiết bị: {updated["device_name"]}
            - Số lượng: {updated["quantity"]}
            - Phương thức vận chuyển: {updated["shipping"]}
            - Phương thức thanh toán: {updated["payment"]}
            - Địa chỉ giao hàng: {updated["address"]}
            - Số điện thoại: {updated["customer_phone"]}
            - Thời gian đặt hàng: {updated["time_reservation"]}

            💳 Tổng tiền sau cập nhật: {updated["price"]}

            Mọi thắc mắc hoặc cần hỗ trợ, vui lòng liên hệ bộ phận chăm sóc khách hàng:

            Tư vấn mua hàng (Miễn phí)  
            📞 1800.6601 (Nhánh 1)

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Cảm ơn bạn đã tin tưởng lựa chọn FPT Shop!

            Trân trọng,  
            Đội ngũ FPT Shop  
            https://fptshop.com.vn
            """
    return email_subject, email_body



def send_order_cancel(order_id,customer_name):
    email_subject = "Your FPT Shop Order Has Been Canceled"
    email_body = f"""
        Kính gửi {customer_name},

        Đơn hàng của bạn với mã số {order_id} đã được hủy thành công.

        Nếu bạn không yêu cầu hủy hoặc muốn đặt lại đơn hàng, vui lòng truy cập website của chúng tôi hoặc liên hệ tổng đài hỗ trợ.

        📞 Tư vấn mua hàng (Miễn phí): 1800.6601 (Nhánh 1)  
        🛠 Hỗ trợ kỹ thuật: 1800.6601 (Nhánh 2)  
        📢 Góp ý, khiếu nại: 1800.6616 (8:00 – 22:00)

        Cảm ơn bạn đã tin tưởng FPT Shop!

        Trân trọng,  
        Đội ngũ FPT Shop  
        https://fptshop.com.vn
    ---------------------------ENGLISH VERSION BELOW ---------------------------

        Dear {customer_name},

        Your order with order ID {order_id} has been successfully cancelled.

        If you do not require cancellation or want to place another order, please visit our website or contact our customer support.

        📞 Customer Support (Free Call): 1800.6601 (Call Center 1)
        """
    return email_subject, email_body