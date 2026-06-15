import os
import base64
from typing import Optional, Dict, Any

from imagekitio import ImageKit


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")


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
    """
    Build ImageKit watermark transformation chain.

    If username is None/empty, return an empty transformation safely.
    """
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
    """
    Deprecated / avoid using if your free-tier Video Transformations are exhausted.

    Returning a direct URL here prevents accidental HLS dependency.
    """
    return base_url


def get_thumbnail_url(base_url: str, username: Optional[str] = None) -> str:
    """
    Deprecated for video-derived thumbnails.

    IMPORTANT:
    Do NOT use /ik-thumbnail.jpg because it consumes ImageKit video transformation quota.
    Use an uploaded image URL instead, and keep this only as a compatibility fallback.
    """
    return base_url


def add_image_watermark(base_url: str, username: Optional[str] = None) -> str:
    """
    Apply watermark transformation to an image URL.
    Safe only for images, not video-derived thumbnails.
    """
    transformations = _get_watermark_transformation(username)
    if not transformations:
        return base_url

    if "?tr=" in base_url:
        return f"{base_url},{transformations}"
    return f"{base_url}?tr={transformations}"


# ---------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------
def upload_video(file_data: bytes, file_name: str, folder: str = "videos") -> Dict[str, Any]:
    """
    Upload a video file to ImageKit and return file metadata.

    Expected usage:
    - Save the returned URL as `video_url`
    - Save returned file_id if you want deletion later
    """
    client = get_imagekit_client()

    response = client.files.upload(
        file=file_data,
        file_name=file_name,
        folder=folder,
    )

    return {
        "file_id": response.file_id,
        "url": response.url,
    }


def upload_thumbnail(file_data, file_name: str, folder: str = "thumbnails") -> Dict[str, Any]:
    """
    Upload a thumbnail image.

    Supports:
    - raw bytes
    - base64 string
    - data URL string like: data:image/jpeg;base64,...

    IMPORTANT:
    This should upload a real image, not derive a thumbnail from video.
    """
    if isinstance(file_data, bytes):
        image_bytes = file_data

    elif isinstance(file_data, str):
        if file_data.startswith("data:"):
            base64_data = file_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_bytes = base64.b64decode(file_data)

    else:
        raise TypeError("file_data must be bytes or str (base64/data URL).")

    client = get_imagekit_client()

    response = client.files.upload(
        file=image_bytes,
        file_name=file_name,
        folder=folder,
    )

    return {
        "file_id": response.file_id,
        "url": response.url,
    }


def upload_avatar(file_data, file_name: str, folder: str = "avatars") -> Dict[str, Any]:
    """
    Upload an avatar image.
    Supports bytes or base64/data URL string.
    """
    if isinstance(file_data, bytes):
        image_bytes = file_data

    elif isinstance(file_data, str):
        if file_data.startswith("data:"):
            base64_data = file_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_bytes = base64.b64decode(file_data)

    else:
        raise TypeError("file_data must be bytes or str (base64/data URL).")

    client = get_imagekit_client()

    response = client.files.upload(
        file=image_bytes,
        file_name=file_name,
        folder=folder,
    )

    return {
        "file_id": response.file_id,
        "url": response.url,
    }


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
    """
    Delete an avatar from ImageKit by file_id.
    """
    if not file_id:
        return False

    client = get_imagekit_client()
    try:
        client.files.delete(file_id=file_id)
        return True
    except Exception:
        return False