#!/usr/bin/env python3
"""Send email notification with access details."""
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(url: str, api_key: str) -> bool:
    """Send access details via Gmail."""
    sender = "jtleyba2018@gmail.com"
    receiver = "dogheadhunter@proton.me"
    app_password = "qpeqilqxbvqfjrke"
    
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Fallout Script Review - New Access URL"
    
    body = f"""Your Fallout DJ Script Review app is now accessible!

ACCESS URL:
{url}

API KEY:
{api_key}

Simply open the URL in your browser to review and approve scripts.
The API key is already configured in the app.

Note: This URL changes each time the server restarts.

---
Auto-generated notification
"""
    
    msg.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        send_email(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python send_email.py <url> <api_key>")
