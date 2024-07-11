from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from ..schemas import schemas
from ..models.models import User, Teacher, ReactionArticle
from ..schemas import utils
from ..dependencies.dependencies import db_dependency, current_user_dependency
from ..ftp import upload, download, delete
from io import BytesIO
import uuid
import os
import tempfile
import mimetypes
from datetime import datetime

router = APIRouter()


# Upload Article
@router.post("", status_code=status.HTTP_201_CREATED)
async def add_article(
    db: db_dependency,
    current_user: User = current_user_dependency,
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        if current_user.user_type != 1:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        
        if file.content_type not in utils.allowed_image_mime_types:
            raise HTTPException(status_code=403, detail="File harus bertipe image, yaa")

        content = await file.read()
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"
       
        new_article = ReactionArticle(
            title=title,
            filename=unique_filename,
            description=description,
            author_id=current_user.user_id,
            approval_status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        upload(unique_filename, content, isArticle=True)
        return {"message": "Artikel telah ditambahkan!", "status": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get My Articles
@router.get("", status_code=status.HTTP_200_OK)
async def get_my_articles(
    db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    articles = (
        db.query(ReactionArticle).filter(ReactionArticle.author_id == current_user.user_id).all()
    )
    if not articles:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")

    sorted_articles = sorted(articles, key=lambda x: x.updated_at, reverse=True)
    return sorted_articles


# Get All Approved Article
@router.get("/approved", status_code=status.HTTP_200_OK)
async def get_all_approved_articles(
    db: db_dependency, current_user: User = current_user_dependency
):
    articles = db.query(ReactionArticle).filter(ReactionArticle.approval_status == "APPROVED").all()
    if not articles:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")

    approved_articles_schema = []

    for a in articles:
        user = db.query(User).filter(User.user_id == a.author_id).first()
        approved_articles_schema.append(schemas.ArticleView(
            title=a.title,
            author_name=user.full_name,
            description=a.description,
            updated_at=a.updated_at,
            article_id=a.article_id
        ))

    articles_sorted = sorted(approved_articles_schema, key=lambda x: x.updated_at, reverse=True)
    
    return articles_sorted


# Get Detailed Article
@router.get("/{articleId}", status_code=status.HTTP_200_OK)
async def get_article_detail(
    articleId: int, db: db_dependency, current_user: User = current_user_dependency
):
    is_valid = False
    if utils.is_valid_Authorization(current_user.email):
        is_valid = True

    if not is_valid:
        article = (
            db.query(ReactionArticle)
            .filter(
                ReactionArticle.article_id == articleId,
            )
            .first()
        )
        if not article:
            raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")
        if article.approval_status != "APPROVED" and article.author_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

        return {"article_item": article}
    else:
        article = db.query(ReactionArticle).filter(ReactionArticle.article_id == articleId).first()
        if not article:
            raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")

        user = db.query(User).filter(User.user_id == article.author_id).first()
        user_nip = (
            db.query(Teacher).filter(Teacher.teacher_id == user.user_id).first().nip
        )

        detail = schemas.ArticleReview(
            article_id=articleId,
            title=article.title,
            filename=article.filename,
            description=article.description,
            author_username=user.username,
            author_nip=user_nip
        )
        return {"article_review": detail}


@router.get("/{articleId}/content")
async def view_content(articleId: int, db: db_dependency):
    article = (
        db.query(ReactionArticle)
        .filter(
            ReactionArticle.article_id == articleId,
        )
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")
    try:
        content = download(article.filename, isArticle=True)
        media_type, _ = mimetypes.guess_type(article.filename)
        return StreamingResponse(BytesIO(content), media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Update Article
@router.put("/{articleId}", status_code=status.HTTP_200_OK)
async def update_my_article(
    articleId: int,
    db: db_dependency,
    current_user: User = current_user_dependency,
    title: str = Form(default=None),
    description: str = Form(default=None),
    file: UploadFile = File(default=None),
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    if file.content_type not in utils.allowed_image_mime_types:
            raise HTTPException(status_code=403, detail="File harus bertipe image, yaa")

    article = db.query(ReactionArticle).filter(ReactionArticle.article_id == articleId).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artkel tidak ditemukan!")

    if article.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")


    unique_filename = None
    new_article = None
    if file is not None:
        content = await file.read()
        file_extension = file.filename.split(".")[-1]
        if file_extension == "":
            raise HTTPException(status_code=400, detail="File tidak valid!")
        unique_filename = f"{uuid.uuid4().hex[:5]}.{file_extension}"
        

    if (
        title is not None
        or unique_filename is not None
        or description is not None
    ):
        new_article = ReactionArticle(
            title=title,
            filename=unique_filename,
            description=description,
        )

    if new_article is None:
        raise HTTPException(status_code=400, detail="Tidak ada yang diupdate!")

    if new_article.title is not None:
        article.title = new_article.title
    if new_article.description is not None:
        article.description = new_article.description
    if new_article.filename is not None:
        delete(article.filename, isArticle=True)
        upload(unique_filename, content, isArticle=True)
        article.filename = new_article.filename

    article.approval_status = "PENDING"
    article.updated_at = datetime.now()
    db.commit()
    return {"message": "Artikel telah diperbarui!", "status": True}


# Delete Artikel
@router.delete("/{articleId}", status_code=status.HTTP_200_OK)
async def delete_my_article(
    articleId: int, db: db_dependency, current_user: User = current_user_dependency
):
    if current_user.user_type != 1:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    article = db.query(ReactionArticle).filter(ReactionArticle.article_id == articleId).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")

    if article.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    db.delete(article)
    db.commit()
    delete(article.filename, isArticle=True)
    return {"message": "Artikel berhasil dihapus!", "status": True}


# Modify Article Status
@router.put("/{articleId}/status", status_code=status.HTTP_200_OK)
async def modify_article_status(
    articleId: int,
    status: str,
    db: db_dependency,
    current_user: User = current_user_dependency,
):
    is_valid = False

    if utils.is_valid_Authorization(current_user.email):
        is_valid = True
    else:
        raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")

    article = db.query(ReactionArticle).filter(ReactionArticle.article_id == articleId).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan!")

    if status == "APPROVED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        article.approval_status = status
        article.updated_at = datetime.now()
        db.commit()
        return {"message": "Artikel berhasil di terima!", "status": True}
    elif status == "REJECTED":
        if not is_valid:
            raise HTTPException(status_code=403, detail="Akun ini tidak diberi ijin!")
        article.approval_status = status
        article.updated_at = datetime.now()
        db.commit()
        return {"message": "Artikel berhasil di tolak!", "status": True}
    else:
        raise HTTPException(status_code=400, detail="Status tidak valid!")
