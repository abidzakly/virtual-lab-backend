from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from ..schemas import schemas
from ..models.models import Material, User, Teacher
from ..schemas import utils
from ..dependencies.dependencies import db_dependency, current_user_dependency
from ..ftp import upload, download, delete
from io import BytesIO
import uuid
import os
import moviepy.editor as mp
import tempfile
import mimetypes
from datetime import datetime

router = APIRouter()


# Upload Materi
@router.post("", status_code=status.HTTP_201_CREATED)
async def add_materi(
    db: db_dependency,
    current_user: User = current_user_dependency,
    title: str = Form(...),
    media_type: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        if current_user.user_type != 1:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

        if media_type != "image":
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_extension}"
            ) as input_file:
                input_file.write(await file.read())
                input_file_path = input_file.name
            compressed_file_path = f"{tempfile.gettempdir()}/compressed_{unique_filename}"

            utils.compress_video(input_file_path, compressed_file_path)
            
            with open(compressed_file_path, "rb") as buffer:
                content = buffer.read()
        else:
            content = await file.read()
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

        if media_type != "image":
            if media_type != "video":
                raise HTTPException(status_code=400, detail="Media type tidak valid!")
        
        db_materi = Material(
            title=title,
            media_type=media_type,
            filename=unique_filename,
            description=description,
            author_id=current_user.user_id,
            approval_status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(db_materi)
        db.commit()
        db.refresh(db_materi)
        upload(unique_filename, content, True)
        return {"message": "Materi telah ditambahkan!", "status": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get My Materi
@router.get("", status_code=status.HTTP_200_OK)
async def get_my_materials(
    db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    materials = (
        db.query(Material).filter(Material.author_id == current_user.user_id).all()
    )
    if not materials:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

    sorted_materials = sorted(materials, key=lambda x: x.created_at, reverse=True)
    return sorted_materials


# Get All Approved Materi
@router.get("/approved", status_code=status.HTTP_200_OK)
async def get_all_approved_materials(
    db: db_dependency, current_user: User = current_user_dependency
):
    materials = db.query(Material).filter(Material.approval_status == "APPROVED").all()
    if not materials:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")
    
    material_sorted = sorted(materials, key=lambda x: x.created_at, reverse=True)
    
    new_materials = []
    for item in material_sorted:
        modified_material = {
            "material_id": item.material_id,
            "title": item.title,
            "description": item.description
        }
        new_materials.append(modified_material)

    return new_materials


# Get Detailed Materi
@router.get("/{materialId}", status_code=status.HTTP_200_OK)
async def get_detailed_materi(
    materialId: int, db: db_dependency, current_user: User = current_user_dependency
):
    is_valid = False
    if utils.is_valid_Authorization(current_user.email):
        is_valid = True

    if not is_valid:
        material = (
            db.query(Material)
            .filter(
                Material.material_id == materialId,
            )
            .first()
        )
        if not material:
            raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")
        if material.approval_status != "APPROVED" and material.author_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

        return {"materi_item": material}
    else:
        materi = db.query(Material).filter(Material.material_id == materialId).first()
        if not materi:
            raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

        user = db.query(User).filter(User.user_id == materi.author_id).first()
        user_nip = (
            db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first().nip
        )

        detail = schemas.MaterialReview(
            material_id=materialId,
            title=materi.title,
            media_type=materi.media_type,
            filename=materi.filename,
            description=materi.description,
            author_username=user.username,
            author_nip=user_nip,
        )
        return {"materi_review": detail}


@router.get("/{materialId}/content")
async def view_content(materialId: int, db: db_dependency):
    material = (
        db.query(Material)
        .filter(
            Material.material_id == materialId,
        )
        .first()
    )
    try:
        content = download(material.filename, True)
        media_type, _ = mimetypes.guess_type(material.filename)
        return StreamingResponse(BytesIO(content), media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Update Materi
@router.put("/{materialId}", status_code=status.HTTP_200_OK)
async def update_my_materi(
    materialId: int,
    db: db_dependency,
    current_user: User = current_user_dependency,
    title: str = Form(default=None),
    media_type: str = Form(default=None),
    description: str = Form(default=None),
    file: UploadFile = File(default=None),
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    material = db.query(Material).filter(Material.material_id == materialId).first()
    if not material:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

    if material.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")


    unique_filename = None
    db_materi = None
    if file is not None:
        if media_type == "image":
            content = await file.read()
            file_extension = file.filename.split(".")[-1]
            if file_extension == "":
                raise HTTPException(status_code=400, detail="File tidak valid!")
            unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"
        else:
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_extension}"
            ) as input_file:
                input_file.write(await file.read())
                input_file_path = input_file.name
            compressed_file_path = f"{tempfile.gettempdir()}/compressed_{unique_filename}"

            utils.compress_video(input_file_path, compressed_file_path)

            with open(compressed_file_path, "rb") as buffer:
                content = buffer.read()

    if (
        title is not None
        or media_type is not None
        or unique_filename is not None
        or description is not None
    ):
        db_materi = Material(
            title=title,
            media_type=media_type,
            filename=unique_filename,
            description=description,
        )

    if db_materi is None:
        raise HTTPException(status_code=400, detail="Tidak ada yang diupdate!")

    if db_materi.title is not None:
        material.title = db_materi.title
    if media_type is not None and db_materi.filename is None:
        raise HTTPException(status_code=403, detail="Anda harus menyertakan file!")
    if db_materi.description is not None:
        material.description = db_materi.description
    if db_materi.filename is not None:
        if db_materi.media_type is None:
            raise HTTPException(
                status_code=400, detail="Anda tidak menyertakan tipe file!"
            )
        delete(material.filename, True)
        upload(unique_filename, content, True)
        material.filename = db_materi.filename
        material.media_type = db_materi.media_type

    material.approval_status = "PENDING"
    material.updated_at = datetime.now()
    db.commit()
    return {"message": "Materi telah diperbarui!", "status": True}


# Delete Materi
@router.delete("/{materialId}", status_code=status.HTTP_200_OK)
async def delete_my_materi(
    materialId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    material = db.query(Material).filter(Material.material_id == materialId).first()
    if not material:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

    if material.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    db.delete(material)
    delete(material.filename, True)
    db.commit()
    return {"message": "Materi berhasil dihapus!", "status": True}


# Modify material Status
@router.put("/{materialId}/status", status_code=status.HTTP_200_OK)
async def modify_material_status(
    materialId: int,
    status: str,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    is_valid = False

    if utils.is_valid_Authorization(current_user.email):
        is_valid = True
    else:
        # if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    material = db.query(Material).filter(Material.material_id == materialId).first()
    if not material:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

    if status == "APPROVED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        material.approval_status = status
        material.updated_at = datetime.now()
        db.commit()
        return {"message": "Materi berhasil di terima!", "status": True}
    elif status == "REJECTED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        material.approval_status = status
        material.updated_at = datetime.now()
        db.commit()
        return {"message": "Materi berhasil di tolak!", "status": True}
    # elif status == "PENDING":
    #     if material.author_id != current_user.user_id:
    #         raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
    #     material.approval_status = status
    #     db.commit()
    #     return {"message": "Status materi berhasil di update!", "status": True}
    else:
        raise HTTPException(status_code=400, detail="Status tidak valid!")

@router.get("/{materialId}/content/thumbnail")
async def get_video_thumbnail(materialId: int, db: db_dependency):
    materi_content = db.query(Material).filter(Material.material_id == materialId).first()
    try:
        content = download(materi_content.filename, True)
        thumbnail = utils.get_thumbnail(content)
        return StreamingResponse(BytesIO(thumbnail), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
