


from core.config import settings
from itsdangerous import URLSafeTimedSerializer,SignatureExpired, BadSignature
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from core.config import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt


FROM_EMAIL = settings.FROM_EMAIL
SENDGRID_API_KEY = settings.SENDGRID_API_KEY
SECRET_EMAIL_KEY = settings.SECRET_EMAIL_KEY
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_reset_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # shorter expiry for reset tokens
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_reset_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
    

#for email service

serializer = URLSafeTimedSerializer(SECRET_EMAIL_KEY)

def generate_verification_token(email: str) -> str:
    return serializer.dumps(email, salt="email-verification-salt")

def verify_token(token: str, max_age=3600) -> str:
    # from itsdangerous import SignatureExpired, BadSignature
    try:
        email = serializer.loads(token, salt="email-verification-salt", max_age=max_age)
        return email
    except SignatureExpired:
        return "expired"
    except BadSignature:
        return "invalid"
