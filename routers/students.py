from fastapi import APIRouter, HTTPException, status
from ..schemas import schemas
from ..models.models import (
    StudentAnswer,
    StudentExerciseResult,
    Question,
    Exercise,
    User
)
from ..schemas import utils
from ..dependencies.dependencies import db_dependency, current_user_dependency
from datetime import datetime

router = APIRouter()


# Add Student Answers
@router.post(
    "/exercises/{exerciseId}/answers", status_code=status.HTTP_201_CREATED
)
async def submit_student_answers(
    exerciseId: int,
    request: schemas.SubmitExerciseRequest,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    if current_user.user_type != 0:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin.")
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
            status_code=403, detail="Anda sudah menyelesaikan latihan ini."
        )

    # Get the exercise and questions
    exercise = db.query(Exercise).filter(Exercise.exercise_id == exerciseId).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Latihan tidak ditemukan.")

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
                        question=question.question_text,
                        selected_option=selected_keys,
                        correct_option=correct_keys,
                        correct=True,
                    )
                )
            else:
                answer_results.append(
                    schemas.AnswerResult(
                        question_id=question.question_id,
                        question=question.question_text,
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

    return schemas.SubmitExerciseResponse(
        answer_results=answer_results, score=score_percentage
    )


# Get Student Result
@router.get("/{studentId}/results", status_code=status.HTTP_200_OK)
async def get_student_all_results(studentId: int, db: db_dependency):
    results = db.query(StudentExerciseResult).filter(StudentExerciseResult.student_id == studentId).all()
    if not results:
        raise HTTPException(status_code=404, detail="Hasil tidak ditemukan.")
    sorted_results = sorted(results, key=lambda x: x.completion_date, reverse=True)
    return sorted_results


# Get Student Answers
@router.get(
    "/{studentId}/results/{resultId}", status_code=status.HTTP_200_OK
)
async def get_student_result_of_an_exercise(
    studentId: int, resultId: int, db: db_dependency
):
    results = (
        db.query(StudentExerciseResult)
        .filter(
            StudentExerciseResult.student_id == studentId,
            StudentExerciseResult.result_id == resultId
        )
        .first()
    )
    if not results:
        raise HTTPException(status_code=404, detail="Hasil tidak ditemukan.")
    answers = (
        db.query(StudentAnswer)
        .filter(StudentAnswer.result_id == results.result_id)
        .all()
    )
    if not answers:
        raise HTTPException(status_code=404, detail="Jawaban tidak ditemukan.")
    
    answer_results = []
    for answer in answers:
        answer_results.append(
            schemas.AnswerResult(
                question_id=answer.question_id,
                question=answer.question.question_text,
                selected_option=answer.selected_option,
                correct_option=answer.question.answer_keys,
                correct=answer.is_correct
            )
        )
    return schemas.SubmitExerciseResponse(
        answer_results=answer_results, score=results.score
    )


# # Get Detailed Student Answers
# @router.get("/{studentId}/exercises/{exerciseId}/answers/{answerId}", status_code=status.HTTP_200_OK)
# async def get_student_answers(userId: int, db: db_dependency):
#     student = db.query(Student).filter(Student.student_id == userId).first()
#     if not student:
#         raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
#     return student


# # Add Student Result
# @router.post(
#     "/{studentId}/exercises/{exerciseId}/result", status_code=status.HTTP_200_OK
# )
# async def add_student_result(userId: int, db: db_dependency):
#     student = db.query(Student).filter(Student.student_id == userId).first()
#     if not student:
#         raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
#     return student


# # Get Student Result
# @router.get(
#     "/{studentId}/exercises/{exerciseId}/result", status_code=status.HTTP_200_OK
# )
# async def get_detailed_student_result(userId: int, db: db_dependency):
#     student = db.query(Student).filter(Student.student_id == userId).first()
#     if not student:
#         raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
#     return student
