from fastapi import Depends
from ..database.database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]