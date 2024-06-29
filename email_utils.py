import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
receiver_email = os.getenv("RECEIVER_EMAIL")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))

def send_email(body):
    """
    Sends an email with the provided body text.

    Args:
        body: The body of the email message.
    """
    # Create the container email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'Email from BookMyParking'

    # Attach the body of the email to the MIME message
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the SMTP server and secure the connection
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully")
    except smtplib.SMTPException as e:
        # Handle specific SMTP errors
        print(f"Failed to send email: {e}")
    except ssl.SSLError as e:
        # Handle SSL errors
        print(f"SSL error: {e}")
    except Exception as e:
        # Catch any other unexpected exceptions
        print(f"Unexpected error: {e}")
