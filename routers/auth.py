from fastapi import APIRouter, HTTPException, status
from ..schemas import schemas, utils
from ..models import models
from ..dependencies.dependencies import (
    db_dependency,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token
)
from datetime import timedelta
from jose import JWTError, jwt


router = APIRouter()


# Register
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    student: schemas.StudentCreate | None,
    teacher: schemas.TeacherCreate | None,
    user: schemas.UserCreate,
    db: db_dependency,
):
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
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.user_type == 1:
        new_teacher = models.Teacher(teacher_id=new_user.user_id, nip=teacher.nip)
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
    else:
        new_student = models.Student(student_id=new_user.user_id, nisn=student.nisn)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

    return {
        "message": "Register berhasil. Harap tunggu aktivasi admin.",
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
            status_code=400, detail="Nama pengguna atau password salah! error 1"
        )
    
    if not utils.verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=400, detail="Nama pengguna atau password salah! error 2"
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

    access_token = create_access_token(data={"sub": db_user.username})
    # refresh_token = create_refresh_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        # "refresh_token": refresh_token,
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
