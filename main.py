from fastapi import FastAPI
from .ftp import FTP_HOST, FTP_USER, FTP_PASS, FTP
from .database import database
from .routers import articles, exercises, materials, users, students, auth, introduction
from .models import models
from contextlib import asynccontextmanager
import asyncio


models.Base.metadata.create_all(bind=database.engine)
@asynccontextmanager
async def lifespan(app: FastAPI):
    async def keep_alive():
        while True:
            with FTP(FTP_HOST) as ftp:
                ftp.login(FTP_USER, FTP_PASS)
                ftp.voidcmd("NOOP")
            with database.SessionLocal() as db:
                # Send a simple query to keep the connection alive
                db.execute("SELECT 1")
            await asyncio.sleep(900)  # Keep-alive every 15 minutes (900 seconds)

    # Create a background task to keep the connection alive
    task = asyncio.create_task(keep_alive())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI()


app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(materials.router, prefix="/v1/materials", tags=["materials"])
app.include_router(exercises.router, prefix="/v1/exercises", tags=["exercises"])
app.include_router(students.router, prefix="/v1", tags=["students"])
app.include_router(introduction.router, prefix="/v1/introduction", tags=["introduction"])
app.include_router(articles.router, prefix="/v1/articles", tags=["articles"])

@app.get("/")
async def root():
    return {"message": "Hello World"}