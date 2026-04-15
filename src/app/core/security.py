from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import logging
from passlib.context import CryptContext
from app.core.config import settings
import smtplib
from email.message import EmailMessage


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"
logger = logging.getLogger(__name__)

def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


# This is quite slow +- 200ms
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def send_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    # Placeholder for sending email logic
    print(f"Sending email to {to_email} with subject '{subject}'")
    try:
        msg = EmailMessage()
        msg["From"] = settings.SMTP_DEFAULT_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            logger.info(f"Sending email to {to_email} with subject '{subject}'")
            server.send_message(msg=msg)
    except Exception as e:
        print(f"Failed to send email: {e}")