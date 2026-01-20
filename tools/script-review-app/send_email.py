#!/usr/bin/env python3
"""
Send email notification with cloudflared tunnel URL
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os


def send_tunnel_email(tunnel_url: str, recipient: str = "dogheadhunter@proton.me"):
    """
    Send email with tunnel URL using Gmail SMTP (or other provider)
    
    Environment variables needed:
    - EMAIL_SENDER: Your email address
    - EMAIL_PASSWORD: App-specific password or regular password
    - SMTP_SERVER: SMTP server (default: smtp.gmail.com)
    - SMTP_PORT: SMTP port (default: 587)
    """
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    if not sender or not password:
        print("ERROR: EMAIL_SENDER and EMAIL_PASSWORD environment variables must be set")
        print("\nFor ProtonMail (Paid plans with SMTP access):")
        print('   $env:EMAIL_SENDER = "your-email@proton.me"')
        print('   $env:EMAIL_PASSWORD = "your-protonmail-password"')
        print('   $env:SMTP_SERVER = "smtp.proton.me"')
        print('   $env:SMTP_PORT = "587"')
        print("\nFor ProtonMail Bridge (Free/Paid - Local Bridge required):")
        print('   Install ProtonMail Bridge from https://proton.me/mail/bridge')
        print('   $env:SMTP_SERVER = "127.0.0.1"')
        print('   $env:SMTP_PORT = "1025"')
        print('   Use the Bridge-generated password, not your ProtonMail password')
        print("\nFor Outlook/Hotmail (No app password needed):")
        print('   $env:EMAIL_SENDER = "your-email@outlook.com"')
        print('   $env:EMAIL_PASSWORD = "your-regular-password"')
        print('   $env:SMTP_SERVER = "smtp-mail.outlook.com"')
        print('   $env:SMTP_PORT = "587"')
        print("\nFor Gmail (Requires 2FA + app password):")
        print('   $env:EMAIL_SENDER = "your-email@gmail.com"')
        print('   $env:EMAIL_PASSWORD = "your-app-password"')
        return False
    
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚀 Script Review App - Cloudflare Tunnel Active"
    msg["From"] = sender
    msg["To"] = recipient
    
    # Create HTML and text versions
    text = f"""
Script Review App is now accessible!

Click here to access the app:
{tunnel_url}

This temporary tunnel will remain active until you stop the script.

Happy reviewing! 🎭
"""
    
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #2563eb;">🚀 Script Review App is Live!</h2>
    <p style="font-size: 16px;">Your temporary Cloudflare tunnel is now active.</p>
    <div style="margin: 30px 0;">
      <a href="{tunnel_url}" 
         style="display: inline-block; padding: 15px 30px; background-color: #2563eb; 
                color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
        🎭 Open Script Review App
      </a>
    </div>
    <p style="color: #666; font-size: 14px;">
      URL: <a href="{tunnel_url}">{tunnel_url}</a>
    </p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #999; font-size: 12px;">
      This tunnel will remain active until you stop the script.<br>
      Press Ctrl+C in the terminal to stop the tunnel.
    </p>
  </body>
</html>
"""
    
    # Attach both versions
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email
    try:
        print(f"Sending email to {recipient}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"✅ Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_email.py <tunnel_url>")
        sys.exit(1)
    
    tunnel_url = sys.argv[1]
    success = send_tunnel_email(tunnel_url)
    sys.exit(0 if success else 1)
