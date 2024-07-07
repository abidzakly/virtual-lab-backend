from passlib.context import CryptContext
from typing import List
from ..schemas import schemas
from ..models.models import Material, Exercise, User
from ..dependencies.dependencies import db_dependency
import os, dotenv
from io import BytesIO
from PIL import Image
from fastapi import HTTPException
import cv2
import tempfile

dotenv.load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_valid_Authorization(authorization: str) -> bool:
    return authorization == os.getenv("AUTHORIZATION")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_recent_posts(
    materi: List[Material], latihan: List[Exercise]
) -> List[schemas.RecentPostData]:
    recent_posts = []

    for m in materi:
        recent_posts.append(
            schemas.RecentPostData(
                title=m.title,
                description=m.description,
                approval_status=m.approval_status,
                created_at=m.created_at,
                post_type="Materi",
                post_id=m.material_id,
            )
        )

    for l in latihan:
        recent_posts.append(
            schemas.RecentPostData(
                title=l.title,
                description=l.difficulty,
                approval_status=l.approval_status,
                created_at=l.created_at,
                post_type="Latihan",
                post_id=l.exercise_id,
            )
        )

    # Sort the recent_posts by created_at in descending order
    sorted_recent_posts = sorted(recent_posts, key=lambda x: x.created_at, reverse=True)

    return sorted_recent_posts


def get_pending_posts(
    materi: List[Material], latihan: List[Exercise], db: db_dependency
) -> List[schemas.PendingPostData]:
    pending_posts = []

    for m in materi:
        username = db.query(User).filter(User.user_id == m.author_id).first().username
        pending_posts.append(
            schemas.PendingPostData(
                author_username=username,
                post_id=m.material_id,
                post_type="Materi",
                created_at=m.created_at,
            )
        )

    for l in latihan:
        username = db.query(User).filter(User.user_id == l.author_id).first().username
        pending_posts.append(
            schemas.PendingPostData(
                author_username=username,
                post_id=l.exercise_id,
                post_type="Latihan",
                created_at=l.created_at,
            )
        )

    # Sort the pending_posts by created_at in descending order
    sorted_pending_posts = sorted(
        pending_posts, key=lambda x: x.created_at, reverse=True
    )

    return sorted_pending_posts


# def compress_video(
#     input_path: str, output_path: str, target_size: int = 10 * 1024 * 1024
# ):
#     clip = mp.VideoFileClip(input_path)
#     clip.write_videofile(output_path, bitrate="500k", codec="libx264")


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
        "-vcodec", "libx264",
        "-preset", "ultrafast",
        "-crf", "33",  # Constant Rate Factor, adjust as needed for quality vs. speed
        "-threads", "4",  # Adjust number of threads based on your CPU capabilities
        "-acodec", "aac",
        "-strict", "experimental",
        output_path
    ]

    subprocess.run(command, check=True)

    return output_path
