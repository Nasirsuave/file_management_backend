from sqlmodel import SQLModel
from datetime import datetime

class FileRead(SQLModel):
    id: int
    filename: str
    filepath: str
    content_type: str
    uploaded_at: datetime


