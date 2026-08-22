import cv2
import numpy as np
from form_layout import CANONICAL_WIDTH, CANONICAL_HEIGHT


def deskew_and_warp(image):
    """Find the largest page-like contour and warp it to the canonical layout."""
    if image is None:
        raise ValueError("Image could not be loaded")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return cv2.resize(image, (CANONICAL_WIDTH, CANONICAL_HEIGHT))

    largest = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    # If page detection is unreliable, simple resize is safer than a bad warp.
    if len(approx) != 4 or cv2.contourArea(approx) < 0.25 * image.shape[0] * image.shape[1]:
        return cv2.resize(image, (CANONICAL_WIDTH, CANONICAL_HEIGHT))

    pts = approx.reshape(4, 2).astype(np.float32)

    # Order points: top-left, top-right, bottom-right, bottom-left.
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    ordered = np.array([
        pts[np.argmin(s)],
        pts[np.argmin(d)],
        pts[np.argmax(s)],
        pts[np.argmax(d)],
    ], dtype=np.float32)

    dst = np.array([
        [0, 0],
        [CANONICAL_WIDTH - 1, 0],
        [CANONICAL_WIDTH - 1, CANONICAL_HEIGHT - 1],
        [0, CANONICAL_HEIGHT - 1],
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(ordered, dst)
    return cv2.warpPerspective(
        image, matrix, (CANONICAL_WIDTH, CANONICAL_HEIGHT)
    )


def prepare_crop(crop):
    """Light preprocessing while preserving handwriting strokes."""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Upscale small handwriting regions before recognition.
    h, w = gray.shape
    if h < 64:
        scale = 64 / h
        gray = cv2.resize(
            gray, (int(w * scale), 64), interpolation=cv2.INTER_CUBIC
        )

    # Mild denoising only; aggressive thresholding can erase pencil strokes.
    gray = cv2.fastNlMeansDenoising(gray, None, 5, 7, 21)
    return gray
