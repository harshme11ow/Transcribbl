import cv2
import numpy as np

from form_layout import (
    CANONICAL_WIDTH,
    CANONICAL_HEIGHT,
)

def deskew_and_warp(image):
    """
    Normalize the scanned page to the standard
    dimensions of the fixed form.
    """
    if image is None:
        raise ValueError("Could not load image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return cv2.resize(image, (CANONICAL_WIDTH, CANONICAL_HEIGHT))

    largest = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(largest, True)
    approximation = cv2.approxPolyDP(largest, 0.02 * perimeter, True)

    image_area = image.shape[0] * image.shape[1]
    MIN_PAGE_AREA_FRACTION = 0.85
    area_fraction = cv2.contourArea(largest) / image_area

    if len(approximation) != 4 or area_fraction < MIN_PAGE_AREA_FRACTION:
        return cv2.resize(image, (CANONICAL_WIDTH, CANONICAL_HEIGHT))

    points = approximation.reshape(4, 2).astype(np.float32)
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).ravel()

    top_left = points[np.argmin(sums)]
    top_right = points[np.argmin(differences)]
    bottom_right = points[np.argmax(sums)]
    bottom_left = points[np.argmax(differences)]

    source = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    destination = np.array([
        [0, 0],
        [CANONICAL_WIDTH - 1, 0],
        [CANONICAL_WIDTH - 1, CANONICAL_HEIGHT - 1],
        [0, CANONICAL_HEIGHT - 1],
    ], dtype=np.float32)

    transform = cv2.getPerspectiveTransform(source, destination)
    return cv2.warpPerspective(image, transform, (CANONICAL_WIDTH, CANONICAL_HEIGHT))


def prepare_crop(crop):
    """
    Prepare one handwriting crop for recognition.
    """
    if crop.size == 0:
        raise ValueError("Empty crop.")

    h, w = crop.shape[:2]
    
    # 1. Shave off the outer 3 pixels to drop printed table grid lines.
    # Because we crop exactly to the cell boundaries, the grid lines are 
    # right on the edge. Shaving 3 pixels ensures they are completely erased.
    margin = 3
    if h > 2 * margin and w > 2 * margin:
        crop = crop[margin:h-margin, margin:w-margin]

    # 2. Add a generous white border. TrOCR requires surrounding whitespace. 
    pad = 16
    padded = cv2.copyMakeBorder(
        crop, pad, pad, pad, pad, 
        cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )

    gray = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    # 3. Enlarge small cells so denoising doesn't destroy the strokes.
    if height < 96:
        scale = 96 / height
        new_width = int(width * scale)
        gray = cv2.resize(gray, (new_width, 96), interpolation=cv2.INTER_CUBIC)

    # 4. Soften the denoising. 'h=3' cleans the background without erasing thin pen strokes.
    gray = cv2.fastNlMeansDenoising(gray, None, 3, 7, 21)

    return gray