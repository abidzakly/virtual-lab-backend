# from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
# from fastapi.responses import StreamingResponse
# from ..schemas import utils
# from ..models.models import PengenalanReaksi, User
# from ..ftp import upload, download, delete
# from ..dependencies.dependencies import db_dependency, current_user_dependency
# from io import BytesIO
# import uuid
# import os
# import moviepy.editor as mp
# import tempfile
# import mimetypes
# from datetime import datetime

# router = APIRouter()


# async def compress_video(unique_filename: str, input_path: str, output_path: str):
#     clip = mp.VideoFileClip(input_path)
#     clip.write_videofile(output_path, bitrate="250k", codec="libx264")
#     with open(output_path, "rb") as buffer:
#         content = buffer.read()
#     upload(unique_filename, content)
    
#     # Hapus file sementara
#     os.remove(input_path)
#     os.remove(output_path)


# @router.post("", status_code=status.HTTP_201_CREATED)
# async def add_introduction(
#     db: db_dependency,
#     current_user: User = current_user_dependency,
#     title: str = Form(...),
#     description: str = Form(...),
#     file: UploadFile = File(...),
# ):
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

#     # content = await file.read()
#     file_extension = file.filename.split(".")[-1]
#     unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

#     new_introduction = PengenalanReaksi(
#         title=title,
#         filename=unique_filename,
#         description=description,
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#     )

#     with tempfile.NamedTemporaryFile(
#         delete=False, suffix=f".{file_extension}"
#     ) as input_file:
#         input_file.write(await file.read())
#         input_file_path = input_file.name

#     compressed_file_path = f"{tempfile.gettempdir()}/compressed_{unique_filename}"

#     # Kompres video
#     compress_video(unique_filename, input_file_path, compressed_file_path)

#     # with open(compressed_file_path, "rb") as buffer:
#     #     content = buffer.read()

#     # Upload compressed video content (sesuaikan dengan fungsi upload Anda)
#     # upload(unique_filename, content)

#     # upload(unique_filename, content)

#     db.add(new_introduction)
#     db.commit()
#     db.refresh(new_introduction)

#     return {
#         "message": "Berhasil! Harap menunggu beberapa saat untuk video terupload!",
#         "status": True,
#     }


# @router.get("", status_code=status.HTTP_201_CREATED)
# async def get_introduction(
#     db: db_dependency,
#     current_user: User = current_user_dependency,
# ):
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")
#     introduction = db.query(PengenalanReaksi).first()
#     if not introduction:
#         raise HTTPException(status_code=404, detail="Data tidak ditemukan.")
#     return introduction


# @router.put("", status_code=status.HTTP_201_CREATED)
# async def update_introduction(
#     db: db_dependency,
#     current_user: User = current_user_dependency,
#     title: str = Form(default=None),
#     description: str = Form(default=None),
#     file: UploadFile = File(default=None),
# ):
#     # return title
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

#     old_intro = db.query(PengenalanReaksi).first()

#     if not old_intro:
#         raise HTTPException(status_code=404, detail="Tidak ada data yang diperbarui.")

#     unique_filename = None
#     new_intro = None
#     if file is not None:
#         content = await file.read()
#         file_extension = file.filename.split(".")[-1]
#         if file_extension == "":
#             raise HTTPException(status_code=400, detail="File tidak valid.")
#         unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"
#         # input_file_path = f"/tmp/{unique_filename}"
#         # compressed_file_path = f"/tmp/compressed_{unique_filename}"

#         # with open(input_file_path, "wb") as buffer:
#         #     shutil.copyfileobj(file.file, buffer)

#         # utils.compress_video(input_file_path, compressed_file_path)

#         # with open(compressed_file_path, "rb") as buffer:
#         #     content = buffer.read()

#     if title is not None or unique_filename is not None or description is not None:
#         new_intro = PengenalanReaksi(
#             title=title,
#             filename=unique_filename,
#             description=description,
#         )

#     if new_intro is None:
#         raise HTTPException(status_code=404, detail="Tidak ada data yang diperbarui.")

#     if new_intro.title is not None:
#         old_intro.title = title

#     if new_intro.description is not None:
#         old_intro.description = description

#     if new_intro.filename is not None:
#         delete(old_intro.filename)
#         upload(unique_filename, content)
#         old_intro.filename = new_intro.filename

#     old_intro.updated_at = datetime.now()
#     db.commit()
#     db.refresh(old_intro)
#     return {"message": "Berhasil memperbarui!", "status": True}


# @router.delete("", status_code=status.HTTP_201_CREATED)
# async def delete_introduction(
#     db: db_dependency,
#     current_user: User = current_user_dependency,
# ):
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

#     introduction = db.query(PengenalanReaksi).first()
#     delete(introduction.filename)
#     db.delete(introduction)
#     db.commit()
#     return {"message": "Berhasil dihapus!", "status": True}


# @router.get("/content")
# async def view_introduction_content(db: db_dependency):
#     introduction_content = db.query(PengenalanReaksi).first()
#     try:
#         media_type, _ = mimetypes.guess_type(introduction_content.filename)
#         content = download(introduction_content.filename)
#         return StreamingResponse(BytesIO(content), media_type=media_type)
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=str(e))


# @router.get("/content/thumbnail")
# async def get_video_thumbnail(db: db_dependency):
#     introduction_content = db.query(PengenalanReaksi).first()
#     try:
#         content = download(introduction_content.filename)
#         thumbnail = utils.get_thumbnail(content)
#         return StreamingResponse(BytesIO(thumbnail), media_type="image/jpeg")
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=str(e))
