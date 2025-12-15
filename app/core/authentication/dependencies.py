from typing import Annotated
from sqlmodel import Session, select
from .hashing import verify_password
from database.session import get_session
from database.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jwt.exceptions import InvalidTokenError
from schemas.token import TokenData
from core.config import settings


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def authenticate_user(session: Session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_user(session: Session, username: str):
    statement = select(User).where(User.username == username)  # or .where(User.email == email) if you use email
    return session.exec(statement).first()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
