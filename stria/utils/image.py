from __future__ import annotations

import base64
import io

import cv2
import numpy as np
from PIL import Image


def bytes_to_numpy(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes to a BGR numpy array (OpenCV format)."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes — unsupported format or corrupted data")
    return img


def numpy_to_bytes(image: np.ndarray, ext: str = ".jpg", quality: int = 92) -> bytes:
    """Encode a numpy array to image bytes."""
    params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext in (".jpg", ".jpeg") else []
    ok, buf = cv2.imencode(ext, image, params)
    if not ok:
        raise ValueError(f"Could not encode image to {ext}")
    return buf.tobytes()


def numpy_to_base64(image: np.ndarray, ext: str = ".jpg", quality: int = 92) -> str:
    """Encode numpy array to a base64 string (for vision API calls)."""
    raw = numpy_to_bytes(image, ext=ext, quality=quality)
    return base64.b64encode(raw).decode("utf-8")


def bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def resize_to_max_edge(image: np.ndarray, max_edge: int = 1600) -> np.ndarray:
    h, w = image.shape[:2]
    if max(h, w) <= max_edge:
        return image
    scale = max_edge / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def validate_image_size(image_bytes: bytes, max_mb: int = 10) -> None:
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"Image too large: {size_mb:.1f} MB (max {max_mb} MB)")
