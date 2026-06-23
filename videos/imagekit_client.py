import os
import base64
from typing import Optional, Dict, Any

from imagekitio import ImageKit

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY", "public_oD7rKxE/GAr5X9k8fEulY3Ix0f8=")
PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY", "private_te6+66a1HnRqRbsgK9ZkF3PTVkY=")
URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT", "https://ik.imagekit.io/6lz1fm648")


# ---------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------
def get_imagekit_client() -> ImageKit:
    """
    Create and return an ImageKit client.

    Note:
    - imagekitio SDK typically requires the private key for server-side uploads/deletes.
    - public_key is usually not necessary for these operations.
    """
    return ImageKit(
        private_key=PRIVATE_KEY
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _get_watermark_transformation(username: Optional[str]):
    # دستور ساخت برچسب (watermark)
    if not username:
        return ""

    return (
        "l-text,"
        f"i-{username},"
        "lfo-bottom_left,"
        "lx-10,ly-10,"
        "fs-32,"
        "co-FFFFFF,"
        "bg-00000060,"
        "pa-4_8,"
        "l-end"
    )


# این تابع لینک ویدیو را می‌گیرد و به ImageKit می‌گه
# "با کیفیت کمتر و فرمت مناسب‌تر پخش کن"
def get_optimized_video_url(base_url: str) -> str:
    """
    Keep this only if you still want a light URL parameter for delivery.
    It does NOT do video frame extraction or HLS.
    """
    if not base_url:
        return base_url

    if "?" in base_url:
        return f"{base_url}&tr=q-50,f-auto"
    return f"{base_url}?tr=q-50,f-auto"


def get_streaming_url(base_url: str) -> str:
    # برای اضافه کردن HLS در اینده
    return base_url


def get_thumbnail_url(base_url: str, username: Optional[str] = None) -> str:
    # این تابع فعلاً فقط لینک ورودی را برمی‌گرداند و هیچ thumbnail واقعی تولید نمی‌کند
    return base_url


def add_image_watermark(base_url: str, username: Optional[str] = None) -> str:
    # چسباندن برچسب روی thumbnail
    transformations = _get_watermark_transformation(username)
    if not transformations:
        return base_url
    # اگر قبلاً transform داشت ادامه بده اگر نداشت بساز
    if "?tr=" in base_url:
        return f"{base_url},{transformations}"
    return f"{base_url}?tr={transformations}"


# ---------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------
def upload_video(file_data: bytes, file_name: str, folder: str = "videos") -> Dict[str, Any]:
    client = get_imagekit_client()
    # فایل ویدیو را می‌فرستد به ImageKit ,اسم فایل را تنظیم می‌کند ,داخل فولدر مشخص ذخیره می‌کند
    response = client.files.upload(
        file=file_data,
        file_name=file_name,
        folder=folder,
    )

    return {
        "file_id": response.file_id,  # شناسه فایل برای حذف یا مدیریت
        "url": response.url,  # شناسه فایل برای حذف یا مدیریت
    }


# این قسمت فقط وظیفه‌اش اینه که هر نوع ورودی تصویر رو به bytes تبدیل کنه تا آماده آپلود بشه.
# یک تابع کمکی (private) برای آپلود عکس.
def _upload_image(file_data, file_name: str, folder: str) -> Dict[str, Any]:
    # بررسی می‌کند آیا ورودی از قبل bytes هست یا نه
    if isinstance(file_data, bytes):
        image_bytes = file_data

    # اگر ورودی رشته (string) بود وارد این بخش می‌شود.
    elif isinstance(file_data, str):
        # بررسی می‌کند آیا رشته از نوع Data URL است یا نه
        if file_data.startswith("data:"):
            base64_data = file_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_bytes = base64.b64decode(file_data)

    else:
        raise TypeError(
            "file must be bytes or str (base64/data URL)."
        )

    # اتصال به ImageKit
    client = get_imagekit_client()

    # آپلود
    response = client.files.upload(
        file=image_bytes,
        file_name=file_name,
        folder=folder,
    )

    # اطلاعات فایل آپلود شده را برمی‌گرداند
    return {
        "file_id": response.file_id,
        "url": response.url,
    }

#wrapper
def upload_thumbnail(
        file_data,
        file_name: str,
        folder: str = "thumbnails"
) -> Dict[str, Any]:
    return _upload_image(file_data, file_name, folder)


def upload_avatar(
        file_data,
        file_name: str,
        folder: str = "avatars"
) -> Dict[str, Any]: #type hint
    return _upload_image(file_data, file_name, folder)


# ---------------------------------------------------------------------
# Deletes
# ---------------------------------------------------------------------
def delete_video(file_id: str) -> bool:
    if not file_id:
        return False

    client = get_imagekit_client()
    client.files.delete(file_id=file_id)
    return True


def delete_avatar(file_id: str) -> bool:
    if not file_id:
        return False

    client = get_imagekit_client()
    try:
        client.files.delete(file_id=file_id)
        return True
    except Exception:
        return False
