from fastapi import APIRouter, HTTPException, status
from ..schemas import schemas, utils
from ..models.models import Exercise, Question, User, Teacher, StudentExerciseResult
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
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    if latihan.question_count <= 0:
        raise HTTPException(status_code=403, detail="Jumlah soal harus lebih dari 0!")

    if latihan.question_count > 10:
        raise HTTPException(status_code=403, detail="Jumlah soal melebihi batas!")

    if (
        latihan.difficulty.lower() != "mudah"
        and latihan.difficulty.lower() != "sedang"
        and latihan.difficulty.lower() != "sulit"
    ):
        raise HTTPException(status_code=403, detail="Tingkat kesulitan tidak valid!")

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
    return {"message": "Latihan berhasil ditambahkan!", "status": True, "data": latihan.exercise_id }



# Get My Exercises
@router.get("", status_code=status.HTTP_200_OK)
async def get_my_exercises(
    db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    latihans = (
        db.query(Exercise).filter(Exercise.author_id == current_user.user_id).all()
    )
    if not latihans:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

    sorted_exercises = sorted(latihans, key=lambda x: x.updated_at, reverse=True)
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
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    db_exercise = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()

    if not db_exercise:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

    if db_exercise.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

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
        raise HTTPException(status_code=403, detail="Jumlah soal melebihi batas!")

    db_exercise.approval_status = "PENDING"
    db_exercise.updated_at = datetime.now()
    db.commit()

    for new_soal in new_soal_list:
        db.refresh(new_soal)
    return {"message": "Soal berhasil ditambahkan!", "status": True}



# Update Soal
@router.put("/{exerciseId}/questions", status_code=status.HTTP_200_OK)
async def update_soal(
    exerciseId: int,
    soal: list[schemas.QuestionUpdate],
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
    
    exercise = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    
    if not exercise:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")
    
    if exercise.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
    
    db_soal = db.query(Question).filter(Question.exercise_id == exerciseId)

    new_soal_list = []
    for new_soal in db_soal.all():
        for item in soal:
            if (new_soal.question_id == item.question_id):
                new_soal.question_text = item.question_text
                new_soal.answer_keys = item.answer_keys
                new_soal.option_text = item.option_text
                db.add(new_soal)
                new_soal_list.append(new_soal)

    exercise.updated_at = datetime.now()
    exercise.approval_status = "PENDING"
    db.commit()

    for updated_soal in new_soal_list:
        db.refresh(updated_soal)
    return {"message": "Soal berhasil diperbarui!", "status": True}



# Get All Latihan
@router.get("/approved", status_code=status.HTTP_200_OK)
async def get_all_approved_exercise(
    db: db_dependency, current_user: User = current_user_dependency
):
    exercise = db.query(Exercise).filter(Exercise.approval_status == "APPROVED").all()
    if not exercise:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan!")

    exercise_sorted = sorted(exercise, key=lambda x: x.updated_at, reverse=True)

    new_exercise = []
    for item in exercise_sorted:
        result = (
            db.query(StudentExerciseResult)
            .filter(
                StudentExerciseResult.exercise_id == item.exercise_id,
                StudentExerciseResult.student_id == current_user.user_id,
            )
            .first()
        )
        if not result:
            modified_exercise = {
                "exercise_id": item.exercise_id,
                "title": item.title,
                "difficulty": item.difficulty,
            }
            new_exercise.append(modified_exercise)

    return new_exercise



# Get Detail Latihan
@router.get("/{exerciseId}", status_code=status.HTTP_200_OK)
async def get_my_detail_latihan(
    exerciseId: int, db: db_dependency, current_user: User = current_user_dependency
):
    is_valid = False
    if current_user.user_type != 1:
        if not utils.is_valid_Authorization(current_user.email):
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        else:
            is_valid = True

    if not is_valid:
        latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
        if not latihan:
            raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

        if (
            latihan.author_id != current_user.user_id
            and not utils.is_valid_Authorization(current_user.email)
        ):
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

        
        is_results_exist = False
        
        check_existing_results = db.query(StudentExerciseResult).filter(
            StudentExerciseResult.exercise_id == exerciseId
        ).first()

        if check_existing_results:
            is_results_exist = True


        soal = db.query(Question).filter(Question.exercise_id == exerciseId).all()

        return {"latihan": latihan, "soal": soal, "is_results_exist": is_results_exist}
    else:
        latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
        if not latihan:
            raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

        user = db.query(User).filter(User.user_id == latihan.author_id).first()
        user_nip = (
            db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first().nip
        )

        detail = schemas.ExerciseReview(
            exercise_id=exerciseId,
            title=latihan.title,
            question_count=latihan.question_count,
            author_username=user.username,
            author_nip=user_nip,
            difficulty=latihan.difficulty,
        )
        return {"latihan_review": detail}



# Update Latihan
@router.put("/{exerciseId}", status_code=status.HTTP_200_OK)
async def update_latihan(
    exerciseId: int,
    is_updating_soal: bool,
    latihan: schemas.ExerciseUpdate,
    db: db_dependency,
    is_resetting_results: bool = False,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
    
    new_latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId)
    
    if not new_latihan:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")
    
    if new_latihan.first().author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    if is_resetting_results:
        db.query(StudentExerciseResult).filter(
            StudentExerciseResult.exercise_id == exerciseId        
        ).delete()


    new_latihan.first().updated_at = datetime.now()
    
    if is_updating_soal:
        new_latihan.first().approval_status = 'DRAFT'
    else:
        new_latihan.first().approval_status = 'PENDING'
    
    new_latihan.update(latihan.model_dump())
    
    db.commit()
    # db.refresh(new_latihan)
    return {"message": "Latihan berhasil diperbarui!", "status": True}



# Delete Latihan
@router.delete("/{exerciseId}", status_code=status.HTTP_200_OK)
async def delete_my_latihan(
    exerciseId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()

    if not latihan:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan")

    if latihan.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    db.delete(latihan)
    db.commit()
    return {"message": "Latihan berhasil di hapus!", "status": True}



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
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    latihan = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    if not latihan:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

    if status == "APPROVED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        latihan.approval_status = status
        latihan.updated_at = datetime.now()
        db.commit()
        return {"message": "Latihan berhasil di terima!", "status": True}
    elif status == "REJECTED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
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
        raise HTTPException(status_code=400, detail="Status tidak valid!")