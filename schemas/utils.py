from fastapi import Form
from passlib.context import CryptContext
from typing import List
from ..schemas import schemas
from ..models.models import Material, Exercise, User, ReactionArticle
from ..dependencies.dependencies import db_dependency
import os, dotenv
from io import BytesIO
from PIL import Image
from fastapi import HTTPException
import cv2
import tempfile
import smtplib
from email.message import EmailMessage

dotenv.load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
allowed_image_mime_types = {
        "image/jpeg", "image/png", "image/gif", "image/jpg", "image/webp", "image/avif"
    }
allowed_video_mime_types = {
    "video/mp4", "video/mpeg", "video/x-msvideo", "video/x-ms-wmv", "video/quicktime", "video/webm"
}

VIDEO_MAX_SIZE = 150 * 1024 * 1024

def is_valid_Authorization(authorization: str) -> bool:
    return authorization == os.getenv("AUTHORIZATION")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_recent_posts(
    article: List[ReactionArticle], materi: List[Material], latihan: List[Exercise]
) -> List[schemas.RecentPostData]:
    recent_posts = []

    for a in article:
        recent_posts.append(
            schemas.RecentPostData(
                title=a.title,
                description=a.description,
                approval_status=a.approval_status,
                updated_at=a.updated_at,
                post_type="Artikel",
                post_id=a.article_id
            )
        )


    for m in materi:
        recent_posts.append(
            schemas.RecentPostData(
                title=m.title,
                description=m.description,
                approval_status=m.approval_status,
                updated_at=m.updated_at,
                post_type="Materi",
                post_id=m.material_id
            )
        )

    for l in latihan:
        recent_posts.append(
            schemas.RecentPostData(
                title=l.title,
                description=l.difficulty,
                approval_status=l.approval_status,
                updated_at=l.updated_at,
                post_type="Latihan",
                post_id=l.exercise_id
            )
        )

    # Sort the recent_posts by created_at in descending order
    sorted_recent_posts = sorted(recent_posts, key=lambda x: x.updated_at, reverse=True)

    return sorted_recent_posts

def get_pending_posts(
    article: List[ReactionArticle], materi: List[Material], latihan: List[Exercise], db: db_dependency
) -> List[schemas.PendingPostData]:
    pending_posts = []

    for a in article:
        username = db.query(User).filter(User.user_id == a.author_id).first().username
        pending_posts.append(
            schemas.PendingPostData(
                author_username=username,
                post_id=a.article_id,
                post_type="Artikel",
                updated_at=a.updated_at
            )
        )

    for m in materi:
        username = db.query(User).filter(User.user_id == m.author_id).first().username
        pending_posts.append(
            schemas.PendingPostData(
                author_username=username,
                post_id=m.material_id,
                post_type="Materi",
                updated_at=m.updated_at
            )
        )

    for l in latihan:
        username = db.query(User).filter(User.user_id == l.author_id).first().username
        pending_posts.append(
            schemas.PendingPostData(
                author_username=username,
                post_id=l.exercise_id,
                post_type="Latihan",
                updated_at=l.updated_at
            )
        )

    # Sort the pending_posts by created_at in descending order
    sorted_pending_posts = sorted(
        pending_posts, key=lambda x: x.updated_at, reverse=True
    )

    return sorted_pending_posts

def get_thumbnail(video_bytes: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False) as temp_video:
        temp_video.write(video_bytes)
        temp_video_path = temp_video.name

    # Use cv2.VideoCapture to read the video file
    cap = cv2.VideoCapture(temp_video_path)
    success, frame = cap.read()
    cap.release()
    os.remove(temp_video_path)

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to capture frame from video!"
        )

    # Convert the frame to a PIL image
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    # Save the frame to a BytesIO object
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    return img_byte_arr.read()

def compress_video(input_path: str, output_path: str):
    import subprocess
    # Save the video using FFmpeg with additional options
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vcodec", "libx265",
        "-preset", "ultrafast",
        "-crf", "33",  # Constant Rate Factor, adjust as needed for quality vs. speed
        "-threads", "4",  # Adjust number of threads based on your CPU capabilities
        "-acodec", "aac",
        "-strict", "experimental",
        output_path
    ]

    subprocess.run(command, check=True)

    return output_path

def send_email(is_approved: bool, name : str = Form(), client_email : str = Form(), password : str = Form()):
    email_address = os.getenv("SMTP_EMAIL") # type Email
    email_password = os.getenv("SMTP_PASS") # If you do not have a gmail apps password, create a new app with using generate password. Check your apps and passwords https://myaccount.google.com/apppasswords
    subject = "" 
    if is_approved: 
        subject = "Password akun Virtual Lab anda" 
    else:
        subject = "Terkait Permohonan akun Virtual Lab anda"
    # create email
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = client_email # type Email
    if is_approved:
        msg.set_content(
        f"""\
        Halo {name},
        Selamat, anda telah di approve oleh admin.    
        Password untuk akun Virtual Lab Anda adalah:
        {password}

        Admin Virtual Lab
        """,
        )
    else:
        msg.set_content(
        f"""\
        Halo {name},
        Setelah meninjau akun anda,
        Kami memutuskan untuk menolak permohonan akun anda.

        Admin Virtual Lab
        """,
        )
    # send email
    with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)
 
    return "email successfully sent"

def check_video_size_limit(video_path: str) -> bool:
    file_size = os.path.getsize(video_path)
    if file_size > VIDEO_MAX_SIZE:
        os.remove(video_path)
        return False
    else:
        return True