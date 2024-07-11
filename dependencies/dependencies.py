from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from typing import Annotated, Generator, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from ftplib import FTP
import os, dotenv

from ..database.database import SessionLocal
from ..models import models
from ..schemas import schemas

dotenv.load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator:
    async with SessionLocal() as session:
        yield session

def get_ftp_connection() -> Generator:
    ftp = FTP(os.getenv("FTP_HOST"))
    ftp.login(user=os.getenv("FTP_USER"), passwd=os.getenv("FTP_PASS"))
    try:
        yield ftp
    finally:
        ftp.quit()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token telah expired!")
    except JWTError:
        raise credentials_exception
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme)
                     , db: Session = Depends(get_db)
                     ):
    credentials_exception = HTTPException(
        status_code=401, detail="Tidak dapat mengenali akun!"
    )
    token_data = verify_token(token, credentials_exception)   
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_token_data_for_video(token: str = Depends(oauth2_scheme)
                     , db: Session = Depends(get_db)
                     ):
    credentials_exception = HTTPException(
        status_code=401, detail="Tidak dapat mengenali akun!"
    )
    token_data = verify_token(token, credentials_exception)
    return token_data

current_user_dependency = Depends(get_current_user)
introduction_dependency = Depends(get_token_data_for_video)
db_dependency = Annotated[Session, Depends(get_db)]
ftp_connection = Depends(get_ftp_connection)
async_db_dependency = Annotated[AsyncGenerator, Depends(get_async_db)]