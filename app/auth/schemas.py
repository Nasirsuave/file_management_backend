from sqlmodel import SQLModel
from pydantic import BaseModel
from typing import Optional

class UserCreate(SQLModel):
    username:str
    email: str
    full_name: Optional[str] = None
    password: str  # raw password, will be hashed before storing

# For sending data back to client (without sensitive info)
class UserRead(SQLModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    disabled: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    username:str | None = None


class PasswordReset(BaseModel):
    new_password: str

class ResetPasswordEmail(BaseModel):
    email: str