from ftplib import FTP
from io import BytesIO
import os
import dotenv

dotenv.load_dotenv()

FTP_HOST = os.getenv("FTP_HOST")
FTP_TEACHER = os.getenv("FTP_TEACHER")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

def upload(filename: str, content: bytes, isTeacher: bool = False) -> bool: 
    with FTP(FTP_HOST) as ftp:
        if isTeacher:
            ftp.login(FTP_TEACHER, FTP_PASS)
        else:
            ftp.login(FTP_USER, FTP_PASS)
        with BytesIO(content) as file:
            ftp.storbinary(f"STOR {filename}", file)
            return True

def download(filename: str, isTeacher: bool = False) -> bytes:
    with FTP(FTP_HOST) as ftp:
        if isTeacher:
            ftp.login(FTP_TEACHER, FTP_PASS)
        else:
            ftp.login(FTP_USER, FTP_PASS)
        with BytesIO() as file:
            ftp.retrbinary(f"RETR {filename}", file.write)
            file.seek(0)
            return file.read()
        

def delete(filename: str, isTeacher: bool = False):
    with FTP(FTP_HOST) as ftp:
        if isTeacher:
            ftp.login(FTP_TEACHER, FTP_PASS)
        else:
            ftp.login(FTP_USER, FTP_PASS)
        ftp.delete(filename)
        