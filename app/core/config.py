from pydantic_settings import BaseSettings





class Settings(BaseSettings):
    # Read from .env
    SENDGRID_API_KEY: str
    SECRET_KEY: str
    FROM_EMAIL: str
    SECRET_EMAIL_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "manage_file/uploads"

    ALLOWED_CONTENT_TYPES: set[str] = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    
    class Config:
        env_file = ".env"


settings = Settings()

