from fastapi import FastAPI
from .database import database
from .routers import users
from .models import models

app = FastAPI()
models.Base.metadata.create_all(bind=database.engine)

app.include_router(users.router, prefix="/users", tags=["users"])


