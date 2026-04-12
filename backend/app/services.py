import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config

def send_otp_email(to_email, otp):
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print(f"==================================================")
        print(f"MOCK EMAIL: OTP for {to_email} is: {otp}")
        print(f"==================================================")
        return True

    msg = MIMEMultipart()
    msg['From'] = Config.SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = "Your Career.AI Verification Code"

    body = f"Hello,\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nBest,\nCareer.AI Team"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(Config.SMTP_USERNAME, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
