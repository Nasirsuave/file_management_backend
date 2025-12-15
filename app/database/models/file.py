

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class FileStore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    original_filename: str
    stored_filename: str
    filepath: str
    content_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    owner: "User" = Relationship(back_populates="files")

