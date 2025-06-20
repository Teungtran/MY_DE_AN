import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
from config.base_config import APP_CONFIG
email_config = APP_CONFIG.email_config
EMAIL_USER = email_config.email
SMTP_SERVER = email_config.server
EMAIL_PASSWORD = email_config.password
SMTP_PORT = 587
def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
