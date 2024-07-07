from sqlalchemy import Column, Integer, String, Enum, Text, ForeignKey, TIMESTAMP, JSON, Float, Boolean
from sqlalchemy.orm import relationship, declarative_base
from ..database.database import Base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), default="")
    user_type = Column(Integer, nullable=False)
    registration_status = Column(Enum('PENDING', 'APPROVED'), default='PENDING')
    school = Column(String(255), nullable=False)
    registration_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Teacher(Base):
    __tablename__ = 'Teachers'
    teacher_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    nip = Column(String(255), unique=True, nullable=False)
    user = relationship("User", backref="teacher", cascade="all, delete")

class Student(Base):
    __tablename__ = 'Students'
    student_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    nisn = Column(String(255), unique=True, nullable=False)
    user = relationship("User", backref="student", cascade="all, delete")

class Material(Base):
    __tablename__ = 'Materials'
    material_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    media_type = Column(Enum('image', 'video'), nullable=False)
    filename = Column(String(255), nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey('Users.user_id'))
    approval_status = Column(Enum('PENDING', 'APPROVED', 'REJECTED', 'DRAFT'), default='PENDING')
    author = relationship("User", backref="materials")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Exercise(Base):
    __tablename__ = 'Exercises'
    exercise_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    difficulty = Column(Enum('Mudah', 'Sedang', 'Sulit'), nullable=False)
    question_count = Column(Integer, nullable=False)
    author_id = Column(Integer, ForeignKey('Users.user_id'))
    approval_status = Column(Enum('PENDING', 'APPROVED', 'REJECTED', 'DRAFT'), default='PENDING')
    questions = relationship("Question", backref="exercise", cascade="all, delete-orphan", passive_deletes=True)
    author = relationship("User", backref="exercise")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class Question(Base):
    __tablename__ = 'Questions'
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(Integer, ForeignKey('Exercises.exercise_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    option_text = Column(JSON, nullable=False)
    answer_keys = Column(JSON, nullable=False)
    # exercise = relationship("Exercise", backref="question")

# class Option(Base):
#     __tablename__ = 'Options'
#     option_id = Column(Integer, primary_key=True, autoincrement=True)
#     question_id = Column(Integer, ForeignKey('Questions.question_id'), nullable=False)
#     question = relationship("Question", backref="options")

class StudentExerciseResult(Base):
    __tablename__ = 'StudentExerciseResults'
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('Users.user_id'), nullable=False)
    exercise_id = Column(Integer, ForeignKey('Exercises.exercise_id'), nullable=False)
    score = Column(Float, nullable=False)
    completion_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    student = relationship("User", backref="exercise_results")
    exercise = relationship("Exercise", backref="exercise_results")

class StudentAnswer(Base):
    __tablename__ = 'StudentAnswers'
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey('StudentExerciseResults.result_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey('Questions.question_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    selected_option = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    result = relationship("StudentExerciseResult", backref="answers", cascade="all, delete")
    question = relationship("Question", backref="answers", cascade="all, delete")

class PengenalanReaksi(Base):
    __tablename__ = 'PengenalanReaksi'
    intro_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())