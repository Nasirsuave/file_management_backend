
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class FileStore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    filename: str
    filepath: str
    content_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
