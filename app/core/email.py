from core.config import settings
from itsdangerous import URLSafeTimedSerializer,SignatureExpired, BadSignature
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


FROM_EMAIL = settings.FROM_EMAIL
SENDGRID_API_KEY = settings.SENDGRID_API_KEY
SECRET_EMAIL_KEY = settings.SECRET_EMAIL_KEY



def send_verification_email(to_email: str, verification_link: str):
    """
    Sends an email containing a verification link using SendGrid
    """
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject="Verify Your Email",
        html_content=f"""
        <p>Welcome! Please click the link below to verify your email:</p>
        <a href="{verification_link}">{verification_link}</a>
        <p>This link expires in 1 hour.</p>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")


