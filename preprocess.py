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

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edges = cv2.Canny(
        blur,
        50,
        150
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return cv2.resize(
            image,
            (
                CANONICAL_WIDTH,
                CANONICAL_HEIGHT
            )
        )

    largest = max(
        contours,
        key=cv2.contourArea
    )

    perimeter = cv2.arcLength(
        largest,
        True
    )

    approximation = cv2.approxPolyDP(
        largest,
        0.02 * perimeter,
        True
    )

    # If we cannot confidently detect the page,
    # fall back to resizing.
    if len(approximation) != 4:
        return cv2.resize(
            image,
            (
                CANONICAL_WIDTH,
                CANONICAL_HEIGHT
            )
        )

    points = approximation.reshape(
        4,
        2
    ).astype(np.float32)

    sums = points.sum(axis=1)
    differences = np.diff(
        points,
        axis=1
    ).ravel()

    top_left = points[np.argmin(sums)]
    top_right = points[np.argmin(differences)]
    bottom_right = points[np.argmax(sums)]
    bottom_left = points[np.argmax(differences)]

    source = np.array(
        [
            top_left,
            top_right,
            bottom_right,
            bottom_left,
        ],
        dtype=np.float32
    )

    destination = np.array(
        [
            [0, 0],
            [CANONICAL_WIDTH - 1, 0],
            [
                CANONICAL_WIDTH - 1,
                CANONICAL_HEIGHT - 1
            ],
            [0, CANONICAL_HEIGHT - 1],
        ],
        dtype=np.float32
    )

    transform = cv2.getPerspectiveTransform(
        source,
        destination
    )

    return cv2.warpPerspective(
        image,
        transform,
        (
            CANONICAL_WIDTH,
            CANONICAL_HEIGHT
        )
    )


def prepare_crop(crop):
    """
    Prepare one handwriting crop for recognition.
    """

    if crop.size == 0:
        raise ValueError("Empty crop.")

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    height, width = gray.shape

    # Small cells need to be enlarged.
    if height < 96:

        scale = 96 / height

        new_width = int(
            width * scale
        )

        gray = cv2.resize(
            gray,
            (
                new_width,
                96
            ),
            interpolation=cv2.INTER_CUBIC
        )

    # Mild denoising.
    gray = cv2.fastNlMeansDenoising(
        gray,
        None,
        5,
        7,
        21
    )

    return gray