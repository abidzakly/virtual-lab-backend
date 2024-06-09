from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    full_name: str
    username: str
    user_type: int
    registration_status: Optional[str] = 'PENDING'
    school: str
    registration_date: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: Optional[str] = None

class User(UserBase):
    user_id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class CombinedUser(BaseModel):
    user_id: int
    username: str
    nip: Optional[str] = None
    nisn: Optional[str] = None,

class UpdateStatusRequest(BaseModel):
    user_id: int

class TeacherBase(BaseModel):
    nip: str

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    teacher_id: int

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    nisn: str

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    student_id: int

    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    title: str
    media_type: str
    media_path: str
    description: Optional[str]
    approval_status: Optional[str] = 'pending'

class MaterialCreate(MaterialBase):
    author_id: int

class Material(MaterialBase):
    material_id: int
    author_id: int

    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    title: str
    difficulty: str
    question_count: int
    approval_status: Optional[str] = 'pending'

class ExerciseCreate(ExerciseBase):
    author_id: int

class Exercise(ExerciseBase):
    exercise_id: int
    author_id: int

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_type: str
    question_text: str
    answer_key: str

class QuestionCreate(QuestionBase):
    exercise_id: int

class Question(QuestionBase):
    question_id: int
    exercise_id: int

    class Config:
        from_attributes = True

class OptionBase(BaseModel):
    option_text: str

class OptionCreate(OptionBase):
    question_id: int

class Option(OptionBase):
    option_id: int
    question_id: int

    class Config:
        from_attributes = True

class StudentExerciseResultBase(BaseModel):
    score: int
    completion_date: Optional[datetime]

class StudentExerciseResultCreate(StudentExerciseResultBase):
    student_id: int
    exercise_id: int

class StudentExerciseResult(StudentExerciseResultBase):
    result_id: int
    student_id: int
    exercise_id: int

    class Config:
        from_attributes = True

class StudentAnswerBase(BaseModel):
    selected_option_id: int

class StudentAnswerCreate(StudentAnswerBase):
    result_id: int
    question_id: int

class StudentAnswer(StudentAnswerBase):
    answer_id: int
    result_id: int
    question_id: int

    class Config:
        from_attributes = True

class PengenalanReaksiBase(BaseModel):
    video_path: str
    description: str

class PengenalanReaksiCreate(PengenalanReaksiBase):
    pass

class PengenalanReaksi(PengenalanReaksiBase):
    intro_id: int
    last_updated: datetime

    class Config:
        from_attributes = True
