from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from ..schemas import utils
from ..models.models import PengenalanReaksi, User
from ..ftp import upload
from ..dependencies.dependencies import db_dependency, introduction_dependency, current_user_dependency
import uuid
import os
import moviepy.editor as mp
import tempfile
import ffmpeg
from datetime import datetime

router = APIRouter()

def compress_video(input_path: str, output_path: str):
    clip = mp.VideoFileClip(input_path)
    original_width, original_height = clip.size

    # Maintain the aspect ratio
    new_height = 720  # Example: Setting a fixed height
    new_width = int((original_width / original_height) * new_height)

    clip_resized = clip.resize(newsize=(new_width, new_height))
    
    clip_resized.write_videofile(output_path, bitrate="1000k", codec="libx264")


# def compress_video(input_path: str, output_path: str):
#     import subprocess

#     # Create the VideoFileClip object
#     clip = mp.VideoFileClip(input_path)

#     # Save the video using FFmpeg with additional options
#     command = [
#         "ffmpeg",
#         "-i", input_path,
#         "-vcodec", "libx264",
#         "-preset", "ultrafast",
#         "-crf", "38",  # Constant Rate Factor, adjust as needed for quality vs. speed
#         "-threads", "4",  # Adjust number of threads based on your CPU capabilities
#         "-acodec", "aac",
#         "-strict", "experimental",
#         output_path
#     ]

#     subprocess.run(command, check=True)

#     return output_path

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_test(
    db: db_dependency,
    # current_user: User = current_user_dependency,
    token_check: str = introduction_dependency,
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
):
    # if not utils.is_valid_Authorization(current_user.email):
    #     raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{file_extension}"
    ) as input_file:
        input_file.write(await file.read())
        input_file_path = input_file.name
    compressed_file_path = f"{tempfile.gettempdir()}/compressed_{unique_filename}"

    compress_video(input_file_path, compressed_file_path)
    
    with open(compressed_file_path, "rb") as buffer:
        content = buffer.read()
        
    current_user = db.query(User).filter(User.username == token_check.username).first()
    if not utils.is_valid_Authorization(current_user.email):
        raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

    new_introduction = PengenalanReaksi(
        title=title,
        filename=unique_filename,
        description=description,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db.add(new_introduction)
    db.commit()
    db.refresh(new_introduction)

    if upload(unique_filename, content):
        os.remove(input_file_path)
        os.remove(compressed_file_path)

    
    # Hapus file sementara


    return {
        "message": "Berhasil!",
        "status": True,
    }
# async def upload_video(
#     file: UploadFile,
#     filename: str,
#     file_extension: str,
#     input_file_path: str,
#     compressed_file_path: str,
# ):
#     # Kompres video
#     compress_video(input_file_path, compressed_file_path)

#     with open(compressed_file_path, "rb") as buffer:
#         content = buffer.read()

#     # Upload compressed video content (sesuaikan dengan fungsi upload Anda)
#     upload(filename, content)

#     # Hapus file sementara
#     os.remove(input_file_path)
#     os.remove(compressed_file_path)
