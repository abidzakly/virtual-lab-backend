from fastapi import APIRouter, HTTPException, status
from ..schemas import schemas
from ..models.models import (
    StudentAnswer,
    StudentExerciseResult,
    Question,
    Exercise,
    User,
    Material,
)
from ..dependencies.dependencies import db_dependency, current_user_dependency
from datetime import datetime
from ..schemas import utils

router = APIRouter()


# Add Student Answers
@router.post("/exercises/{exerciseId}/practice", status_code=status.HTTP_201_CREATED)
async def submit_student_answers(
    exerciseId: int,
    request: schemas.SubmitExerciseRequest,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 0:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
    # Check if answers already submitted
    results = (
        db.query(StudentExerciseResult)
        .filter(
            StudentExerciseResult.student_id == current_user.user_id,
            StudentExerciseResult.exercise_id == exerciseId,
        )
        .first()
    )

    if results:
        raise HTTPException(
            status_code=403, detail="Anda sudah menyelesaikan latihan ini!"
        )

    # Get the exercise and questions
    exercise = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan!")

    questions = db.query(Question).filter(Question.exercise_id == exerciseId).all()

    # Calculate the score
    total_score = 0
    answer_results = []
    for answer in request.answers:
        question = next(
            (q for q in questions if q.question_id == answer.question_id), None
        )
        if question:
            selected_keys = answer.selected_option
            correct_keys = question.answer_keys

            if correct_keys == selected_keys:
                total_score += 1  # Full score for correct answer
                answer_results.append(
                    schemas.AnswerResult(
                        question_id=question.question_id,
                        question_title=question.question_text,
                        selected_option=selected_keys,
                        correct_option=correct_keys,
                        correct=True,
                    )
                )
            else:
                answer_results.append(
                    schemas.AnswerResult(
                        question_id=question.question_id,
                        question_title=question.question_text,
                        selected_option=selected_keys,
                        correct_option=correct_keys,
                        correct=False,
                    )
                )

    score_percentage = round((total_score / len(questions)) * 100, 2)

    # Save the result
    result = StudentExerciseResult(
        student_id=current_user.user_id,
        exercise_id=exerciseId,
        score=score_percentage,
        completion_date=datetime.now(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    # Save the student answers
    for answer in request.answers:
        for is_correct in answer_results:
            if answer.question_id == is_correct.question_id:
                student_answer = StudentAnswer(
                    result_id=result.result_id,
                    question_id=answer.question_id,
                    selected_option=answer.selected_option,
                    is_correct=is_correct.correct,
                )
                db.add(student_answer)

    db.commit()

    return {
        "message": "Latihan berhasil diselesaikan!",
        "status": True,
        "data": result.result_id,
    }


# Get Soal for Practice
@router.get("/exercises/{exerciseId}/practice", status_code=status.HTTP_200_OK)
async def get_soal_for_practice(
    exerciseId: int,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 0:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    latihan_check = (
        db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    )
    if latihan_check.approval_status != "APPROVED":
        raise HTTPException(
            status_code=403, detail="Latihan ini tidak memenuhi kriteria!"
        )

    soals = db.query(Question).filter(Question.exercise_id == exerciseId).all()

    if not soals:
        raise HTTPException(status_code=404, detail="Soal tidak ditemukan!")

    new_soal_list = []
    for item in soals:
        answer_key_count = len(item.answer_keys)
        modified_soal = {
            "exercise_id": item.exercise_id,
            "question_title": item.question_text,
            "answer_key_count": answer_key_count,
            "question_id": item.question_id,
            "option_text": item.option_text,
        }
        new_soal_list.append(modified_soal)

    return new_soal_list


# Get Student Result
@router.get("/results", status_code=status.HTTP_200_OK)
async def get_my_results(
    db: db_dependency, current_user: User = current_user_dependency
):
    results = (
        db.query(StudentExerciseResult)
        .filter(StudentExerciseResult.student_id == current_user.user_id).all()
    )
    if not results:
        raise HTTPException(status_code=404, detail="Hasil tidak ditemukan!")
        
    sorted_results = sorted(results, key=lambda x: x.completion_date, reverse=True)
    
    new_results = []
    for result in sorted_results:
        exercise = db.query(Exercise).filter(Exercise.exercise_id == result.exercise_id).first()
        new_results.append(
            schemas.StudentResult(
                result_id=result.result_id,
                title=exercise.title,
                difficulty=exercise.difficulty,
                score=result.score,
            )
        )

    return new_results


# Get Student Answers
@router.get("/results/{resultId}", status_code=status.HTTP_200_OK)
async def get_my_result_detail(
    resultId: int, db: db_dependency, current_user: User = current_user_dependency
):
    results = (
        db.query(StudentExerciseResult)
        .filter(
            StudentExerciseResult.result_id == resultId,
        )
        .first()
    )
    if not results:
        raise HTTPException(status_code=404, detail="Hasil tidak ditemukan!")
    
    if results.student_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Anda tidak diberi ijin!")
    
    answers = (
        db.query(StudentAnswer)
        .filter(StudentAnswer.result_id == results.result_id)
        .all()
    )
    
    if not answers:
        raise HTTPException(status_code=404, detail="Jawaban tidak ditemukan!")

    answer_results = []
    for answer in answers:
        question = db.query(Question).filter(Question.question_id == answer.question_id).first()
        answer_results.append(
            schemas.AnswerResult(
                question_id=answer.question_id,
                question_title=question.question_text,
                selected_option=answer.selected_option,
                correct_option=question.answer_keys,
                correct=answer.is_correct,
            )
        )
    # return answer_results
    return schemas.StudentResultDetail(answers_results=answer_results, score=results.score)