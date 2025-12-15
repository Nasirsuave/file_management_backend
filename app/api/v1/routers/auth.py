from fastapi import FastAPI,HTTPException, Depends, status, APIRouter
from database.models.user import User
from database.models.file import FileStore
from schemas.user import UserCreate
from schemas.token import Token, TokenData 
from schemas.password import PasswordReset,ResetPasswordEmail
from database.session import get_session
from sqlmodel import Session, select, Field
from core.authentication.jwt import create_access_token,create_reset_token,verify_reset_token
from core.authentication.hashing import hash_password,verify_password
from core.email import send_verification_email # needs a bit improvement we should move the function to jwt file 
from core.authentication.jwt import generate_verification_token,verify_token
from core.authentication.dependencies import authenticate_user
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jose import jwt
from jwt.exceptions import InvalidTokenError
# from auth.utils import send_verification_email,generate_verification_token,verify_token
# from itsdangerous import URLSafeTimedSerializer
import os
from core.config import settings




ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY





router = APIRouter()


@router.post("/register")
def register(data: UserCreate, session: Session = Depends(get_session)):
    # check if user exists
    statement = select(User).where(User.email == data.email)
    existing = session.exec(statement).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    token = generate_verification_token(new_user.email)
    verification_link = f"http://localhost:8000/verify-email?token={token}"

    # Send verification email
    send_verification_email(new_user.email, verification_link)

    return {"message": "User registered successfully. Please check your email to verify your account."}




@router.get("/verify-email")
def verify_email(token: str, session: Session = Depends(get_session)):
    email = verify_token(token)
    if email == "expired":
        raise HTTPException(status_code=400, detail="Verification link expired")
    if email == "invalid":
        raise HTTPException(status_code=400, detail="Invalid verification link")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "User already verified"}

    user.is_verified = True
    session.add(user)
    session.commit()
    return {"message": "Email verified successfully. You can now log in."}




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)  # <- inject DB session
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Check your email to verify your account."
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")





@router.post("/forgot-password")
def forgot_password(reset_pass_email: ResetPasswordEmail, session: Session = Depends(get_session) ):
    user = session.query(User).filter(User.email == reset_pass_email.email).first()
    if not user:
        return {"message": "If that email exists, a reset link will be sent"}

    reset_token = create_reset_token({"sub": user.username},expires_delta=timedelta(minutes=15))

    # DEV MODE: return reset link for testing
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"

    return {
        "message": "Password reset requested",
        "reset_link": reset_link  # REMOVE THIS IN PRODUCTION
    }


@router.post("/reset-password")
def reset_password(token: str, password_reset: PasswordReset, session: Session = Depends(get_session)):
    payload = verify_reset_token(token)
    username = payload.get("sub")

    user = session.query(User).filter(User.username == username).first()
    user.hashed_password = hash_password(password_reset.new_password)
    session.commit()


    return {"message": "Password updated successfully"}


