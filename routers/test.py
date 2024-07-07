# from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
# from fastapi.responses import FileResponse
# from ..schemas import utils
# from ..models.models import PengenalanReaksi, User
from ..ftp import upload, download
# from ..dependencies.dependencies import db_dependency, introduction_dependency, current_user_dependency
# import uuid
# import os
# import moviepy.editor as mp
# import tempfile
# import ffmpeg
# from datetime import datetime

# router = APIRouter()

# @router.post("", status_code=status.HTTP_201_CREATED)
# async def add_test(
#     db: db_dependency,
#     current_user: User = current_user_dependency,
#     # token_check: str = introduction_dependency,
#     title: str = Form(...),
#     description: str = Form(...),
#     file: UploadFile = File(...),
# ):
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")
    
#     file_extension = file.filename.split(".")[-1]
#     unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

#     with tempfile.NamedTemporaryFile(
#         delete=False, suffix=f".{file_extension}"
#     ) as input_file:
#         input_file.write(await file.read())
#         input_file_path = input_file.name
#     compressed_file_path = f"{tempfile.gettempdir()}/compressed_{unique_filename}"

#     compress_video(input_file_path, compressed_file_path)
    
#     with open(compressed_file_path, "rb") as buffer:
#         content = buffer.read()
        
#     # current_user = db.query(User).filter(User.username == token_check.username).first()
#     # if not utils.is_valid_Authorization(current_user.email):
#     #     raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

#     new_introduction = PengenalanReaksi(
#         title=title,
#         filename=unique_filename,
#         description=description,
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#     )
    
#     db.add(new_introduction)
#     db.commit()
#     db.refresh(new_introduction)

#     if upload(unique_filename, content):
#         os.remove(input_file_path)
#         os.remove(compressed_file_path)

#     return {
#         "message": "Berhasil!",
#         "status": True,
#     }
# # async def upload_video(
# #     file: UploadFile,
# #     filename: str,
# #     file_extension: str,
# #     input_file_path: str,
# #     compressed_file_path: str,
# # ):
# #     # Kompres video
# #     compress_video(input_file_path, compressed_file_path)

# #     with open(compressed_file_path, "rb") as buffer:
# #         content = buffer.read()

# #     # Upload compressed video content (sesuaikan dengan fungsi upload Anda)
# #     upload(filename, content)

# #     # Hapus file sementara
# #     os.remove(input_file_path)
# #     os.remove(compressed_file_path)
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import moviepy.editor as mp
from io import BytesIO
import os

router = APIRouter()


def compress_video(input_path: str, output_path: str, target_size: int):
    clip = mp.VideoFileClip(input_path)
    width, height = clip.size

    # Determine whether to base the resizing on width or height
    if width > height:  # Landscape
        clip_resized = clip.resize(width=target_size)
    else:  # Portrait
        clip_resized = clip.resize(height=target_size)
    
    clip_resized.write_videofile(output_path, codec='libx264', audio_codec='aac')

@router.post("/compress-video/")
async def compress_video_endpoint(file: UploadFile = File(...)):
    input_path = f"input_{file.filename}"
    output_path = f"output_{file.filename}"

    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())

    # Compress the video to the target size (longer side 1280 pixels)
    target_size = 1280
    compress_video(input_path, output_path, target_size)
    upload(content=open(output_path, "rb").read(), filename=output_path)
        # os.remove(input_path)
        # os.remove(output_path)

    return {"message": "success"}


@router.get("/download-video/")
async def download_video_endpoint(filename: str):
    try:
        content = download(filename)
        return StreamingResponse(BytesIO(content), media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))