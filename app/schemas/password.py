
from sqlmodel import SQLModel
from pydantic import BaseModel
from typing import Optional

class PasswordReset(BaseModel):
    new_password: str

class ResetPasswordEmail(BaseModel):
    email: str