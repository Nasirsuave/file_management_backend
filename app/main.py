
from fastapi import FastAPI,HTTPException, Depends, status

from auth.models import User
from manage_file.models import FileStore
from database import get_session
from auth.schemas import UserCreate, UserRead, Token, TokenData,PasswordReset,ResetPasswordEmail
from sqlmodel import Session, select, Field
from auth.hashing import create_access_token,hash_password,verify_password,create_reset_token,verify_reset_token, ACCESS_TOKEN_EXPIRE_MINUTES,SECRET_KEY,ALGORITHM
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jose import jwt
from jwt.exceptions import InvalidTokenError






app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI running with Docker + PostgreSQL!"}





@app.post("/register")
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

    return {"message": "User registered successfully"}



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.post("/token")
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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")




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



@app.get("/users/me")  #, response_model=User
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user




@app.post("/forgot-password")
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


@app.post("/reset-password")
def reset_password(token: str, password_reset: PasswordReset, session: Session = Depends(get_session)):
    payload = verify_reset_token(token)
    username = payload.get("sub")

    user = session.query(User).filter(User.username == username).first()
    user.hashed_password = hash_password(password_reset.new_password)
    session.commit()


    return {"message": "Password updated successfully"}




#File Management APIs will go here
from fastapi import File, UploadFile
from manage_file.utils import save_upload_file,UPLOAD_DIR
from manage_file.schemas import FileRead
from fastapi.responses import FileResponse
import os 



ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/msword",                             # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}


# Endpoint to upload a file
@app.post("/files/upload")
async def upload_file(
    file: UploadFile,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. "
                   "Allowed types: PDF, PNG, JPEG, DOC, DOCX"
        )
    # ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_location = f"{UPLOAD_DIR}/{file.filename}"

    # save file
    contents = await file.read()
    with open(file_location, "wb") as f:
        f.write(contents)

    db_file = FileStore(
        user_id=current_user.id,
        filename=file.filename,
        filepath=file_location,
        content_type=file.content_type
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)

    return {"message": "File uploaded successfully", "file_id": db_file.id}



# Endpoint to download a file
@app.get("/files/{filename}")
def get_file(filename: str, current_user: User = Depends(get_current_user)):
    filename = filename.strip()
    # file_path = os.path.join(UPLOAD_DIR, filename)
    file_path = f"{UPLOAD_DIR}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)



# Endpoint to delete a file
@app.delete("/files/{filename}")
def delete_file(filename: str, current_user: User = Depends(get_current_user)):

    filename = filename.strip()

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
        return {"message": f"{filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")



# Endpoint to view a file
@app.get("/files/view/{filename}")
def view_file(filename: str):
    filename = filename.strip()  # Avoid newline issues
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")

    # Automatically sets correct media type
    return FileResponse(file_path, media_type="application/octet-stream")