from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from io import BytesIO
from ..schemas import schemas, utils
from ..models.models import User, Teacher, Student, Material, Exercise, ReactionArticle
from ..dependencies.dependencies import db_dependency, current_user_dependency
from ..ftp import upload, download, delete
from datetime import datetime
import uuid


router = APIRouter()


# Get Pending Users
@router.get("/pending", status_code=status.HTTP_200_OK)
async def get_pending_user(
    db: db_dependency, current_user: User = current_user_dependency
):

    if not utils.is_valid_Authorization(current_user.email):
        raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    query = (
        db.query(User, Teacher.nip, Student.nisn)
        .outerjoin(Teacher, Teacher.teacher_id == User.user_id)
        .outerjoin(Student, Student.student_id == User.user_id)
        .filter(User.registration_status == "PENDING")
    )

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")

    combined_users = []
    for user, nip, nisn in results:
        combined_user = schemas.CombinedUser(
            username=user.username,
            user_id=user.user_id,
            nip=nip,
            nisn=nisn,
        )
        combined_users.append(combined_user)

    return combined_users


# Get Detailed User
@router.get("/{userId}", status_code=status.HTTP_200_OK)
async def get_user_by_id(
    userId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_id != userId:
        if not utils.is_valid_Authorization(current_user.email):
            raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    user = db.query(User).filter(User.user_id == userId).first()

    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")

    teacher = (
        db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first()
        if user.user_type == 1
        else None
    )
    student = (
        db.query(Student).filter(Student.student_id == user.user_id).first()
        if user.user_type == 0
        else None
    )

    return {"user": user, "student": student, "teacher": teacher, "status": True}

# Approve
@router.put("/{userId}/approve", status_code=status.HTTP_200_OK)
async def approve_user_registration(
    userId: int,
    password: str,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if not utils.is_valid_Authorization(current_user.email):
        raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    user = db.query(User).filter(User.user_id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")

    user.registration_status = "APPROVED"
    user.password = utils.hash_password(password)
    user.updated_at = datetime.now()
    utils.send_email(name=user.full_name, client_email=user.email, password=password, is_approved=True)
    db.commit()
    return {"message": "Anda berhasil menerima akun ini!", "status": True}


# Disapprove
@router.delete("/{userId}/reject", status_code=status.HTTP_200_OK)
async def reject_user_registration(
    userId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if not utils.is_valid_Authorization(current_user.email):
        raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    user = db.query(User).filter(User.user_id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")

    if user.registration_status == "APPROVED":
        raise HTTPException(
            status_code=403, detail="Tidak dapat menolak, Akun ini sudah di aktivasi!"
        )

    utils.send_email(name=user.full_name, client_email=user.email, password="", is_approved=False)

    if user.user_type == 0:
        student = db.query(Student).filter(Student.student_id == user.user_id).first()
        if student:
            db.delete(student)
        db.delete(user)
        db.commit()
        return {"message": "Anda berhasil menolak akun ini!", "status": True}
    else:
        teacher = db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first()
        if teacher:
            db.delete(teacher)
        db.delete(user)
        db.commit()
        return {"message": "Anda berhasil menolak akun ini!", "status": True}


# Edit Profile User
@router.put("/{userId}", status_code=status.HTTP_200_OK)
async def edit_profile_user(
    userId: int,
    db: db_dependency,
    current_user: User = current_user_dependency,
    old_password: str = Form(...),
    new_password: str = Form(default=None),
    new_email: schemas.EmailStr = Form(default=None),
    file: UploadFile = File(default=None)
):
    unique_filename = None
    if file is not None:
        if file.content_type not in utils.allowed_image_mime_types:
            raise HTTPException(status_code=403, detail="File harus bertipe image, yaa")
        
        content = await file.read()
        file_extension = file.filename.split(".")[-1]
        if file_extension == "":
            raise HTTPException(status_code=400, detail="File tidak valid!")
        unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"
      
    user_query = db.query(User).filter(User.user_id == userId).first()

    is_email_exist = (
        db.query(User).filter(User.email == new_email, User.user_id != userId).first()
    )
    if user_query.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Anda tidak diizinkan!")
    if not user_query:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")
    if is_email_exist:
        raise HTTPException(status_code=403, detail="Email sudah digunakan!")
    if not utils.verify_password(old_password, user_query.password):
        raise HTTPException(status_code=403, detail="Password anda salah!")

    if new_password is None and new_email is None and unique_filename is None:
        raise HTTPException(
            status_code=400, detail="Tidak ada data yang diperbarui!"
        )
    if new_password is not None:
        user_query.password = utils.hash_password(new_password)

    if new_email is not None:
        user_query.email = new_email

    if unique_filename is not None:
        upload(unique_filename, content, isPfp=True)
        user_query.profile_picture = unique_filename

    user_query.updated_at = datetime.now()
    db.commit()
    return {"message": "Profil Anda berhasil diperbarui!", "status": True}


# Get All Materi and All exercise
@router.get("/{teacherId}/posts", status_code=status.HTTP_200_OK)
async def get_recent_posts(
    teacherId: int, db: db_dependency, current_user: User = current_user_dependency
):

    if current_user.user_id != teacherId:
        if not utils.is_valid_Authorization(current_user.email):
            raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    article = (
        db.query(ReactionArticle)
        .filter(ReactionArticle.author_id == teacherId)
        .order_by(ReactionArticle.updated_at.desc())
        .all()
    )

    materi = (
        db.query(Material)
        .filter(Material.author_id == teacherId)
        .order_by(Material.updated_at.desc())
        .all()
    )
    latihan = (
        db.query(Exercise)
        .filter(Exercise.author_id == teacherId)
        .order_by(Exercise.updated_at.desc())
        .all()
    )

    recent_posts = utils.get_recent_posts(article, materi, latihan)

    return recent_posts


# Get All Pending Materi and All Pending exercise
@router.get("/posts/pending", status_code=status.HTTP_200_OK)
async def get_pending_posts(
    db: db_dependency, current_user: User = current_user_dependency
):

    if not utils.is_valid_Authorization(current_user.email):
        raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin!")

    article = (
        db.query(ReactionArticle)
        .filter(ReactionArticle.approval_status == "PENDING")
        .order_by(ReactionArticle.updated_at.desc())
        .all()
    )

    materi = (
        db.query(Material)
        .filter(Material.approval_status == "PENDING")
        .order_by(Material.updated_at.desc())
        .all()
    )
    latihan = (
        db.query(Exercise)
        .filter(Exercise.approval_status == "PENDING")
        .order_by(Exercise.updated_at.desc())
        .all()
    )

    if not article and not materi and not latihan:
        raise HTTPException(status_code=404, detail="Tidak ada postingan!")

    pending_posts = utils.get_pending_posts(article, materi, latihan, db)

    return pending_posts


# Get User's Profile Picture
@router.get("/{userId}/pfp", status_code=status.HTTP_200_OK)
async def get_user_profile_picture(
    userId: int,
    db: db_dependency
):
    user = db.query(User).filter(User.user_id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan!")
    
    try:
        content = download(user.profile_picture, isPfp=True)
        thumbnail = utils.get_thumbnail(content)
        return StreamingResponse(BytesIO(thumbnail), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))