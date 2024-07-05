from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class RecentPostData(BaseModel):
    title: str
    description: Optional[str] = None
    approval_status: str
    created_at: datetime
    post_type: str
    post_id: int

class PendingPostData(BaseModel):
    author_username: str
    post_id: int
    post_type: str
    created_at: datetime

class ExerciseReview(BaseModel):
    title: str
    difficulty: str
    question_count: int
    exercise_id: int
    author_username: str
    author_nip: str

class MaterialReview(BaseModel):
    title: str
    media_type: str
    filename: str
    description: str
    material_id: int
    author_username: str
    author_nip: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    full_name: str
    username: str
    user_type: int
    registration_status: Optional[str] = 'PENDING'
    school: str
    registration_date: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

class UserCreate(UserBase):
    email: EmailStr

class User(UserBase):
    user_id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    updated_at: Optional[datetime] = datetime.now()

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
    filename: str
    description: Optional[str]
    approval_status: Optional[str] = 'DRAFT'

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
    approval_status: Optional[str] = 'DRAFT'
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

class ExerciseCreate(ExerciseBase):
    author_id: Optional[int] = None

class Exercise(ExerciseBase):
    exercise_id: int
    author_id: int

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text: str
    option_text: List[str]
    answer_keys: List[str]

class QuestionCreate(QuestionBase):
    exercise_id: int

class Question(QuestionBase):
    question_id: int
    exercise_id: int

    class Config:
        from_attributes = True

class Answer(BaseModel):
    question_id: int
    selected_option: List[str]

class SubmitExerciseRequest(BaseModel):
    answers: List[Answer]

class AnswerResult(BaseModel):
    question_id: int
    question_title: str
    selected_option: List[str]
    correct_option: List[str]
    correct: bool


class StudentResult(BaseModel):
    result_id: int
    title: str
    difficulty: str
    score: float

class StudentResultDetail(BaseModel):
    answers_results: List[AnswerResult]
    score: float


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
    filename: Optional[str] = None
    title: str
    description: str

class PengenalanReaksiCreate(PengenalanReaksiBase):
    created_at: Optional[datetime] = datetime.now()

class PengenalanReaksiUpdate(BaseModel):
    filename: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = datetime.now()

class PengenalanReaksi(PengenalanReaksiBase):
    intro_id: int
    updated_at: datetime

    class Config:
        from_attributes = True
