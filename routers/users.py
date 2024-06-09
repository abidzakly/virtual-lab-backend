from fastapi import APIRouter, HTTPException, Header, status
from ..schemas import schemas
from ..models import models
from ..schemas import validator
from ..dependencies.dependencies import db_dependency

router = APIRouter()

# Register 
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(student:schemas.StudentCreate | None, teacher: schemas.TeacherCreate | None, user: schemas.UserCreate, db: db_dependency):
    check_username = db.query(models.User).filter(models.User.username == user.username).first()
    if check_username:
        raise HTTPException(status_code=403, detail="Username sudah terdaftar!")

    check_email = db.query(models.User).filter(models.User.email == user.email).first()
    if check_email:
        raise HTTPException(status_code=403, detail="Email sudah terdaftar!")

    check_nip = db.query(models.Teacher).filter(models.Teacher.nip == teacher.nip).first()
    if check_nip:
        raise HTTPException(status_code=403, detail="NIP sudah terdaftar!") 
    
    check_nisn = db.query(models.Student).filter(models.Student.nisn == student.nisn).first()
    if check_nisn:
        raise HTTPException(status_code=403, detail="NISN sudah terdaftar!")

    
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    if new_user.user_type == 1:
        new_teacher = models.Teacher(teacher_id = new_user.user_id, nip = teacher.nip)
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
    else:
        new_student = models.Student(student_id = new_user.user_id, nisn = student.nisn)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

    return {"message": "Register berhasil. Harap tunggu aktivasi admin.", "status": True}

# Login
@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login_request(user: schemas.UserLogin, db: db_dependency): 
    db_user = db.query(models.User).filter(models.User.username == user.username).filter(models.User.password == user.password).first() 

    if db_user is None:
        raise HTTPException(status_code=400, detail="Nama pengguna atau password salah!")
    
    # if not pwd_context.verify(user.password, db_user.hashed_password):
    #     raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if db_user.registration_status == 'PENDING':
        raise HTTPException(status_code=401, detail="Akun belum di aktivasi!")
    
    return db_user


# Get Pending Users
@router.get("/pending", status_code=status.HTTP_201_CREATED)
async def get_all_pending_user(db: db_dependency, authorization: str = Header(default=None)):

    if authorization is None:
        raise HTTPException(status_code=402, detail="Otorisasi diperlukan.")

    if not validator.is_valid_authorization(authorization):
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
    
    query = (
        db.query(models.User, models.Teacher.nip, models.Student.nisn)
        .outerjoin(models.Teacher, models.Teacher.teacher_id == models.User.user_id)
        .outerjoin(models.Student, models.Student.student_id == models.User.user_id)
        .filter(models.User.registration_status == 'PENDING')
    )

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    
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



# Get Pending User
@router.get("/{user_id}", status_code=status.HTTP_201_CREATED)
async def get_user_by_id(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    teacher = db.query(models.Teacher).filter(models.Teacher.teacher_id == user.user_id).first() if user.user_type == 1 else None
    student = db.query(models.Student).filter(models.Student.student_id == user.user_id).first() if user.user_type == 0 else None
    
    return {"user": user, "student": student, "teacher": teacher}

# Approve 
@router.put("/approve", status_code=status.HTTP_201_CREATED)
async def approve_user_request(user_id: int, password: str, db: db_dependency): 
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    
    user.registration_status = 'APPROVED'
    user.password = password

    db.commit()
    return {"message": "Anda menerima akun ini.", "status": True}


# Disapprove 
@router.delete("/reject/{user_id}", status_code=status.HTTP_200_OK)
async def reject_user_request(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    
    if user.registration_status == 'APPROVED':
        raise HTTPException(status_code=401, detail="Tidak dapat menolak, Akun ini sudah di aktivasi.")

    if user.user_type == 0:
        student = db.query(models.Student).filter(models.Student.student_id == user.user_id).first()
        db.delete(student)
        db.delete(user)
        db.commit()
        return {"message": "Anda menolak akun ini.", status: True}