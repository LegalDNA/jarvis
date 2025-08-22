import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL

def send_email(subject: str, html_body: str, text_body: str = None):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        return  # email disabled if not configured

    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject

    if text_body:
        msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [RECIPIENT_EMAIL], msg.as_string())
