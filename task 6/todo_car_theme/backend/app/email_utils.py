import os, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_FROM = os.getenv('EMAIL_FROM', SMTP_USER)

def send_email(to_email: str, subject: str, html_body: str, plain_body: str = None):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        print('⚠️ SMTP not configured; skipping sending email. Check .env.')
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    if plain_body is None:
        plain_body = html_body
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype='html')

    try:
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)

        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print('❌ Email send failed:', e)
        return False
