from fastapi import FastAPI,HTTPException, Depends, status, APIRouter
from database.session import get_session
from sqlmodel import Session, select, Field
from core.authentication.dependencies import get_current_user
from database.models.user import User
from database.models.file import FileStore
from fastapi.responses import FileResponse
from fastapi import File, UploadFile
from core.config import settings
from core.config import settings
import uuid
import os


UPLOAD_DIR = settings.UPLOAD_DIR


router = APIRouter()


# Endpoint to upload a file
@router.post("/files/upload")
async def upload_file(
    file: UploadFile,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # 1️⃣ Validate content type
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}"
        )

    # 2️⃣ Create user-specific directory
    user_upload_dir = os.path.join(
        UPLOAD_DIR,
        "users",
        str(current_user.id)
    )
    os.makedirs(user_upload_dir, exist_ok=True)

    # 3️⃣ Generate unique stored filename
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"

    file_path = os.path.join(user_upload_dir, unique_filename)

    # 4️⃣ Save file to disk
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # 5️⃣ Store metadata in DB
    db_file = FileStore(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=unique_filename,
        filepath=file_path,
        content_type=file.content_type
    )

    session.add(db_file)
    session.commit()
    session.refresh(db_file)

    return {
        "message": "File uploaded successfully",
        "file_id": db_file.id,
        "filename": db_file.original_filename
    }


#Endpoint to download a file
@router.get("/files/{filename}")
def download_file(
    filename: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    
     # 1. Fetch file from DB
    file_record = session.exec(select(FileStore).where(FileStore.original_filename == filename).where(FileStore.user_id == current_user.id)).first()
    

    if not file_record:
        raise HTTPException(status_code=404,detail="File not found or access denied")

    file_path = os.path.join(UPLOAD_DIR, "users", str(file_record.user_id),file_record.stored_filename)
    # 3. Check if actual file exists on disk
    if not os.path.exists(file_path):
        raise HTTPException(status_code=410, detail="File missing on server")

    # 4. Return the file safely
    return FileResponse(
        file_path
    )


#Endpoint to delete a file
@router.delete("/files/{filename}")
def delete_file(
    filename: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    filename = filename.strip()

    # 1. Look up the file by filename AND owner
    file_record = session.exec(
        select(FileStore)
        .where(FileStore.original_filename == filename)
        .where(FileStore.user_id == current_user.id)
    ).first()

     

    if not file_record:
        raise HTTPException(
            status_code=404, 
            detail="File not found or you are not allowed to delete it"
        )

    # 2. Check if file exists on disk
    if not os.path.exists(file_record.filepath):
        # Remove record anyway to avoid DB being out-of-sync
        session.delete(file_record)
        session.commit()

        raise HTTPException(
            status_code=410,
            detail="File already deleted from server"
        )

    # 3. Delete file from disk
    try:
        os.remove(file_record.filepath)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

    # 4. Remove file from DB
    session.delete(file_record)
    session.commit()

    return {"message": f"{filename} deleted successfully"}





#Endpoint to view a file
@router.get("/files/view/{filename}")
def view_file(filename: str):
    filename = filename.strip()  # Avoid newline issues
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")

    # Automatically sets correct media type
    return FileResponse(file_path, media_type="application/octet-stream")


