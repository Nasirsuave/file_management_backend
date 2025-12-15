from fastapi import APIRouter, Depends
from typing import Annotated
from core.authentication.dependencies import get_current_user
from database.models.user import User

router = APIRouter()


@router.get("/users/me")  #, response_model=User
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user