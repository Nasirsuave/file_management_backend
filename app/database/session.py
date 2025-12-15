

from sqlmodel import SQLModel, create_engine, Session
import os

# from app.auth.models import User
# from app.manage_file.models import FileStore


DATABASE_URL = os.getenv("DATABASE_URL")  # reads from environment variable
engine = create_engine(DATABASE_URL, echo=True)

# Create tables
SQLModel.metadata.create_all(engine)

# Dependency
def get_session():
    with Session(engine) as session:
        yield session
