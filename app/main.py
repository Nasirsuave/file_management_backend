
#Routing for the overall well-strucutured project
from fastapi import FastAPI
from api.v1.routers import auth, user, file_management

app = FastAPI()


app.include_router(auth.router, tags=["auth"])
app.include_router(user.router, tags=["users"])
app.include_router(file_management.router, tags=["file_management"])



@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}