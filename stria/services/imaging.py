from __future__ import annotations

import json
import logging

import cv2
import numpy as np

from stria.config import get_settings
from stria.models import BoundingBox, CassetteType, ImageQuality, QualityFailure
from stria.utils.image import bytes_to_numpy, numpy_to_base64, resize_to_max_edge

logger = logging.getLogger(__name__)


def assess_quality(image_bytes: bytes) -> ImageQuality:
    """
    Check blur and exposure. Never raises — returns ImageQuality with acceptable flag.
    """
    settings = get_settings()

    try:
        img = bytes_to_numpy(image_bytes)
    except Exception:
        return ImageQuality(
            blur_score=0.0,
            exposure_ok=False,
            cassette_detected=False,
            acceptable=False,
            failure_reason=QualityFailure.CASSETTE_NOT_FOUND,
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Check exposure FIRST — "image too dark" is more actionable than "image too blurry"
    # when the root cause is lighting. A uniform black/white image has zero Laplacian
    # variance, so blur would be reported incorrectly without this ordering.
    mean_brightness = float(gray.mean())
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if mean_brightness < 40:
        return ImageQuality(
            blur_score=blur_score,
            exposure_ok=False,
            cassette_detected=False,
            acceptable=False,
            failure_reason=QualityFailure.TOO_DARK,
        )
    if mean_brightness > 230:
        return ImageQuality(
            blur_score=blur_score,
            exposure_ok=False,
            cassette_detected=False,
            acceptable=False,
            failure_reason=QualityFailure.TOO_BRIGHT,
        )

    if blur_score < settings.blur_variance_threshold:
        return ImageQuality(
            blur_score=blur_score,
            exposure_ok=True,
            cassette_detected=False,
            acceptable=False,
            failure_reason=QualityFailure.TOO_BLURRY,
        )

    return ImageQuality(
        blur_score=blur_score,
        exposure_ok=True,
        cassette_detected=True,
        acceptable=True,
        failure_reason=None,
    )


def detect_cassette(image_bytes: bytes) -> BoundingBox | None:
    """
    Find the cassette using contour detection filtered by aspect ratio.
    Returns the largest cassette-shaped bounding box, or None.
    """
    img = bytes_to_numpy(image_bytes)
    img = resize_to_max_edge(img, 1600)
    h, w = img.shape[:2]
    image_area = h * w

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best: tuple[float, BoundingBox] | None = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < image_area * 0.04:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        if bh == 0:
            continue
        aspect = bw / bh

        # Accept landscape (3:1–6:1) or portrait (1:3–1:6) cassette shapes
        landscape = 2.5 <= aspect <= 6.0
        portrait = 0.15 <= aspect <= 0.40
        if not (landscape or portrait):
            continue

        if best is None or area > best[0]:
            best = (area, BoundingBox(x=x, y=y, w=bw, h=bh))

    return best[1] if best else None


def extract_result_window(
    image_bytes: bytes,
    bbox: BoundingBox,
    cassette_type: CassetteType,
    brand: str = "default",
) -> np.ndarray:
    """
    Crop the cassette, look up the result window coordinates from
    cassette_profiles.json, crop that sub-region, and apply CLAHE.
    """
    settings = get_settings()
    img = bytes_to_numpy(image_bytes)
    img = resize_to_max_edge(img, 1600)

    ih, iw = img.shape[:2]
    x = max(0, bbox.x)
    y = max(0, bbox.y)
    bw = min(bbox.w, iw - x)
    bh = min(bbox.h, ih - y)
    cassette_crop = img[y : y + bh, x : x + bw]

    try:
        with open(settings.cassette_profiles_path) as f:
            profiles = json.load(f)
        type_profiles = profiles.get(cassette_type.value, {})
        profile = type_profiles.get(brand) or type_profiles.get(
            "default", {"window": {"x": 0.30, "y": 0.10, "w": 0.45, "h": 0.75}}
        )
    except Exception:
        profile = {"window": {"x": 0.30, "y": 0.10, "w": 0.45, "h": 0.75}}

    win = profile["window"]
    ch, cw = cassette_crop.shape[:2]
    wx = max(0, int(win["x"] * cw))
    wy = max(0, int(win["y"] * ch))
    ww = min(int(win["w"] * cw), cw - wx)
    wh = min(int(win["h"] * ch), ch - wy)

    result_window = cassette_crop[wy : wy + wh, wx : wx + ww]
    return _clahe_normalise(result_window)


def _clahe_normalise(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    lab = cv2.merge([l_ch, a_ch, b_ch])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def encode_for_vision(image: np.ndarray) -> str:
    return numpy_to_base64(image, ext=".jpg", quality=92)
