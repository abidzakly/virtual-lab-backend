from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from ..schemas import schemas, utils
from ..models import models
from ..dependencies.dependencies import (
    db_dependency,
    # SECRET_KEY,
    # ALGORITHM,
    # ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    # create_refresh_token
)
# from datetime import timedelta
# from jose import JWTError, jwt


router = APIRouter()


# Register
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    student: schemas.StudentCreate,
    teacher: schemas.TeacherCreate,
    user: schemas.UserCreate,
    db: db_dependency,
):
    if len(user.full_name) > 60:
        raise HTTPException(status_code=400, detail="Nama Lengkap tidak boleh lebih dari 60 karakter!")

    if user.user_type == 1 and teacher.nip is not None:
        if teacher.nip.isnumeric() is False:
            raise HTTPException(status_code=400, detail="NIP harus berupa angka!")
        elif len(teacher.nip) != 9 and len(teacher.nip) != 18:
            raise HTTPException(
                status_code=400, detail="NIP hanya boleh memuat 9 atau 18 angka!"
            )

    if user.email.find("@") == -1 or user.email.find(".") == -1:
        raise HTTPException(status_code=400, detail="Format email tidak benar!")

    if user.user_type == 0 and student.nisn is not None:
        if student.nisn.isnumeric() is False:
            raise HTTPException(status_code=400, detail="NISN harus berupa angka!")
        elif len(student.nisn) != 10:
            raise HTTPException(status_code=400, detail="NISN hanya boleh memuat 10 angka!")

    if len(user.username) < 8 or len(user.username) > 20:
        raise HTTPException(status_code=400, detail="Username harus memuat 8-20 karakter!")

    check_username = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if check_username:
        raise HTTPException(status_code=403, detail="Username sudah terdaftar!")

    check_email = db.query(models.User).filter(models.User.email == user.email).first()
    if check_email:
        raise HTTPException(status_code=403, detail="Email sudah terdaftar!")

    check_nip = (
        db.query(models.Teacher).filter(models.Teacher.nip == teacher.nip).first()
    )
    if check_nip:
        raise HTTPException(status_code=403, detail="NIP sudah terdaftar!")

    check_nisn = (
        db.query(models.Student).filter(models.Student.nisn == student.nisn).first()
    )
    if check_nisn:
        raise HTTPException(status_code=403, detail="NISN sudah terdaftar!")
    
    model_user = models.User(
        username=user.username,
        email=user.email,
        user_type=user.user_type,
        full_name=user.full_name,
        school=user.school,
        registration_status="PENDING",
        registration_date=datetime.now(),
        updated_at=datetime.now(),
    )
 
    db.add(model_user)
    db.commit()
    db.refresh(model_user)

    if model_user.user_type == 1:
        new_teacher = models.Teacher(teacher_id=model_user.user_id, nip=teacher.nip)
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
    else:
        new_student = models.Student(student_id=model_user.user_id, nisn=student.nisn)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

    return {
        "message": "Register berhasil! Harap tunggu aktivasi admin.",
        "status": True,
    }


# Login
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: schemas.UserLogin, db: db_dependency):
    db_user = (
        db.query(models.User)
        .filter(models.User.username == user.username)
        .first()
    )

    if db_user is None:
        raise HTTPException(
            status_code=400, detail="Nama pengguna atau password salah!"
        )
    
    if not utils.verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=400, detail="Nama pengguna atau password salah!"
        )
    
    if db_user.registration_status == "PENDING":
        raise HTTPException(status_code=401, detail="Akun belum di aktivasi!")

    teacher = (
        db.query(models.Teacher)
        .filter(models.Teacher.teacher_id == db_user.user_id)
        .first()
        if db_user.user_type == 1
        else None
    )
    student = (
        db.query(models.Student)
        .filter(models.Student.student_id == db_user.user_id)
        .first()
        if db_user.user_type == 0
        else None
    )
    
    intro_title = db.query(models.PengenalanReaksi).first()
    if intro_title is None:
        intro_title = "Pengenalan Reaksi"
    else:
        intro_title = intro_title.title
    access_token = create_access_token(data={"sub": db_user.username})
    # refresh_token = create_refresh_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        # "refresh_token": refresh_token,
        "intro_title": intro_title,
        "user": db_user,
        "student": student,
        "teacher": teacher,
    }


# @router.post("/token/refresh", response_model=schemas.TokenData)
# async def refresh_token(refresh_token: str, db: db_dependency):
#     # Validate the refresh token
#     try:
#         payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid refresh token")
#         token_data = schemas.TokenData(username=username)
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")

#     # Generate a new access token
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     new_access_token = create_access_token(
#         data={"sub": token_data.username}, expires_delta=access_token_expires
#     )

#     return {"access_token": new_access_token, "token_type": "bearer"}
