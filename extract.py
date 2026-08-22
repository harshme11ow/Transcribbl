import re
import cv2
from dataclasses import asdict
from form_layout import (
    HEADER_FIELDS, COLUMNS, ROW_START_Y, ROW_HEIGHT, MAX_ROWS,
    SKIP_FIRST_DATA_ROW, NUMERIC_FIELDS
)
from preprocess import prepare_crop


def crop(image, box):
    x1, y1, x2, y2 = box
    return image[y1:y2, x1:x2]


def recognize_region(recognizer, image, box):
    region = crop(image, box)
    prepared = prepare_crop(region)
    return recognizer.recognize(prepared)


def normalize_numeric(text):
    # Conservative cleanup. Do not aggressively "correct" uncertain values.
    cleaned = text.strip().replace(" ", "")
    cleaned = cleaned.replace("O", "0").replace("o", "0")
    return cleaned


def field_review_needed(field, text, confidence):
    if not text:
        return True

    if field in NUMERIC_FIELDS:
        candidate = normalize_numeric(text)
        # Accept normal integers, decimals, or a leading minus sign.
        if not re.fullmatch(r"-?\d+(\.\d+)?", candidate):
            return True

    return confidence < 0.82


def extract_page(image, recognizer, page_number=1):
    results = []
    review_items = []

    for field, box in HEADER_FIELDS.items():
        r = recognize_region(recognizer, image, box)
        results.append({
            "page": page_number,
            "field": field,
            "row": None,
            "text": r.text,
            "confidence": r.confidence,
        })
        if field_review_needed(field, r.text, r.confidence):
            review_items.append(results[-1])

    first_row = 1 if SKIP_FIRST_DATA_ROW else 0

    for row in range(first_row, MAX_ROWS):
        y1 = ROW_START_Y + row * ROW_HEIGHT
        y2 = y1 + ROW_HEIGHT - 1

        for field, col_box in COLUMNS.items():
            x1, _, x2, _ = col_box
            box = (x1, y1, x2, y2)
            r = recognize_region(recognizer, image, box)

            # Skip truly empty cells. This is intentionally simple for v1.
            if not r.text and r.confidence < 0.2:
                continue

            item = {
                "page": page_number,
                "field": field,
                "row": row,
                "text": r.text,
                "confidence": r.confidence,
            }
            results.append(item)

            if field_review_needed(field, r.text, r.confidence):
                review_items.append(item)

    return results, review_items
