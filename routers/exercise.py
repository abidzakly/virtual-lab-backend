from fastapi import APIRouter, HTTPException, status
from ..schemas import schemas, utils
from ..models.models import Exercise, Question, User, Teacher
from ..dependencies.dependencies import db_dependency, current_user_dependency
from datetime import datetime

router = APIRouter()


# Upload Exercise
@router.post("", status_code=status.HTTP_201_CREATED)
async def add_latihan(
    latihan: schemas.ExerciseCreate,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    if latihan.question_count <= 0:
        raise HTTPException(status_code=403, detail="Jumlah soal harus lebih dari 0")

    if latihan.question_count > 10:
        raise HTTPException(status_code=403, detail="Jumlah soal melebihi batas")
    
    if latihan.difficulty != "mudah" and latihan.difficulty != "sedang" and latihan.difficulty != "sulit":
        raise HTTPException(status_code=403, detail="Tingkat kesulitan tidak valid")

    latihan.author_id = current_user.user_id
    new_latihan = Exercise(**latihan.model_dump())
    db.add(new_latihan)
    db.commit()
    db.refresh(new_latihan)

    latihan = (
        db.query(Exercise)
        .filter(Exercise.exercise_id == new_latihan.exercise_id)
        .first()
    )
    return latihan


# Get All Latihan by Author
@router.get("", status_code=status.HTTP_200_OK)
async def get_all_latihan_by_author(
    db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    latihans = (
        db.query(Exercise).filter(Exercise.author_id == current_user.user_id).all()
    )
    if not latihans:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

    sorted_exercises = sorted(latihans, key=lambda x: x.created_at, reverse=True)
    return sorted_exercises


# Upload Soal
@router.post("/{exerciseId}/questions", status_code=status.HTTP_201_CREATED)
async def add_soal(
    exerciseId: int,
    soal: list[schemas.QuestionCreate],
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    db_exercise = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()

    if not db_exercise:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

    if db_exercise.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    soal_existed = db.query(Question).filter(Question.exercise_id == exerciseId).count()
    new_soal_list = []
    for item in soal:
        item.exercise_id = exerciseId
        new_soal = Question(**item.model_dump())
        db.add(new_soal)
        new_soal_list.append(new_soal)

    if len(new_soal_list) > db_exercise.question_count or len(new_soal_list) > (
        db_exercise.question_count - soal_existed
    ):
        raise HTTPException(status_code=403, detail="Jumlah soal melebihi batas")

    db_exercise.approval_status = "PENDING"
    db_exercise.updated_at = datetime.now()
    db.commit()

    for new_soal in new_soal_list:
        db.refresh(new_soal)
    return {"message": "Soal telah ditambahkan", "status": True}


# Get Soal by Exercise ID
@router.get("/{exerciseId}/questions", status_code=status.HTTP_200_OK)
async def get_soal_by_exercise_id(
    exerciseId: int,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    soals = db.query(Question).filter(Question.exercise_id == exerciseId).all()

    if not soals:
        raise HTTPException(status_code=404, detail="Soal tidak ditemukan")

    new_soal_list = []
    for item in soals:
        answer_key_count = len(item.answer_keys)
        modified_soal = {
            "exercise_id": item.exercise_id,
            "question_text": item.question_text,
            "answer_key_count": answer_key_count,
            "question_id": item.question_id,
            "option_text": item.option_text
        }
        new_soal_list.append(modified_soal)

    return new_soal_list
    # if soals[0].


# # Get All Pending Latihan
# @router.get("/pending", status_code=status.HTTP_200_OK)
# async def get_pending_latihan(
#     db: db_dependency, current_user: User = current_user_dependency
# ):
#     if not utils.is_valid_Authorization(current_user.email):
#         raise HTTPException(status_code=401, detail="Akun ini tidak diberi ijin.")

#     latihans = db.query(Exercise).filter(Exercise.approval_status == "PENDING").all()
#     if not latihans:
#         raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")
    
#     sorted_exercises = sorted(latihans, key=lambda x: x.created_at, reverse=True)
#     return sorted_exercises


# Get Detail Latihan
@router.get("/{exerciseId}", status_code=status.HTTP_200_OK)
async def get_detail_latihan(
    exerciseId: int, db: db_dependency, current_user: User = current_user_dependency
):
    is_valid = False
    if current_user.user_type != 1:
        if not utils.is_valid_Authorization(current_user.email):
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
        else: 
            is_valid = True

    if not is_valid:
        latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
        if not latihan:
            raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

        if (
            latihan.author_id != current_user.user_id
            and not utils.is_valid_Authorization(current_user.email)
        ):
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

        soal = db.query(Question).filter(Question.exercise_id == exerciseId).all()

        return {"latihan": latihan, "soal": soal}
    else:
        latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
        if not latihan:
            raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

        user = db.query(User).filter(User.user_id == latihan.author_id).first()
        user_nip = db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first().nip

        detail = schemas.ExerciseReview(
            exercise_id=exerciseId,
            title=latihan.title,
            question_count=latihan.question_count,
            author_username=user.username,
            author_nip=user_nip,
            difficulty=latihan.difficulty
        )
        return {"latihan_review": detail }


# Modify Exercise Status
@router.put("/{exerciseId}/status", status_code=status.HTTP_200_OK)
async def modify_exercise_status(
    exerciseId: int,
    status: str,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    is_valid = False

    if utils.is_valid_Authorization(current_user.email):
        is_valid = True
    else:
        # if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    if not latihan:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

    if status == "APPROVED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
        latihan.approval_status = status
        latihan.updated_at = datetime.now()
        db.commit()
        return {"message": "Latihan berhasil di terima!", "status": True}
    elif status == "REJECTED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
        latihan.approval_status = status
        latihan.updated_at = datetime.now()
        db.commit()
        return {"message": "Latihan berhasil di tolak!", "status": True}
    # elif status == "PENDING" or status == "DRAFT":
    #     if latihan.author_id != current_user.user_id:
    #         raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
    #     latihan.approval_status = status
    #     db.commit()
    #     return {"message": "Status latihan berhasil di update!", "status": True}
    else:
        raise HTTPException(status_code=400, detail="Status tidak valid")


# Delete Latihan
@router.delete("/{exerciseId}", status_code=status.HTTP_200_OK)
async def delete_latihan(
    exerciseId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    
    if not latihan:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")
    
    if latihan.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")

    db.delete(latihan)
    db.commit()
    return {"message": "Latihan di hapus", "status": True}