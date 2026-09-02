import re

from form_layout import (
    HEADER_FIELDS,
    COLUMNS,
    ROW_START_Y,
    ROW_HEIGHT,
    MAX_ROWS,
    SKIP_FIRST_DATA_ROW,
    NUMERIC_FIELDS,
    MANUAL_REVIEW_THRESHOLD,
)

from preprocess import prepare_crop, is_blank


def crop_image(
    image,
    box,
    padding_x=0,
    padding_y=0
):
    x1, y1, x2, y2 = box

    x1 = max(0, x1 - padding_x)
    y1 = max(0, y1 - padding_y)
    x2 = min(image.shape[1], x2 + padding_x)
    y2 = min(image.shape[0], y2 + padding_y)

    return image[
        y1:y2,
        x1:x2
    ]


def recognize_region(
    recognizer,
    image,
    box,
    padding_x=0,
    padding_y=0
):
    crop = crop_image(
        image,
        box,
        padding_x,
        padding_y
    )
    
    # If the cell is empty, bypass TrOCR to stop hallucinations
    if is_blank(crop):
        class EmptyResult:
            text = ""
            confidence = 1.0
        return EmptyResult()

    prepared = prepare_crop(
        crop
    )

    return recognizer.recognize(
        prepared
    )


def normalize_numeric(text):

    return (
        text.strip()
        .replace(" ", "")
        .replace("O", "0")
        .replace("o", "0")
    )


def field_review_needed(
    field,
    text,
    confidence
):

    if not text:

        return True

    if field in NUMERIC_FIELDS:

        candidate = normalize_numeric(
            text
        )

        if not re.fullmatch(
            r"-?\d+(\.\d+)?",
            candidate
        ):

            return True

    return (
        confidence
        < MANUAL_REVIEW_THRESHOLD
    )


def extract_page(
    image,
    recognizer,
    page_number=1,
    progress_callback=None
):

    results = []

    review_items = []

    first_row = (
        1
        if SKIP_FIRST_DATA_ROW
        else 0
    )

    total_jobs = (
        len(HEADER_FIELDS)
        +
        (
            MAX_ROWS - first_row
        )
        *
        len(COLUMNS)
    )

    completed_jobs = 0


    # -------------------------
    # HEADER FIELDS
    # -------------------------

    for field, box in (
        HEADER_FIELDS.items()
    ):
        # Headers need generous padding so ascenders/descenders are not cut off
        recognition = recognize_region(
            recognizer,
            image,
            box,
            padding_x=12,
            padding_y=12
        )

        item = {
            "page": page_number,
            "field": field,
            "row": None,
            "text": recognition.text,
            "confidence": recognition.confidence,
            "box": list(box),
        }

        results.append(item)

        if field_review_needed(field, recognition.text, recognition.confidence):
            review_items.append(item)

        completed_jobs += 1

        if progress_callback:
            progress_callback(
                completed_jobs,
                total_jobs,
                "Reading " + field.replace("_", " ")
            )


    # -------------------------
    # TABLE FIELDS
    # -------------------------

    for row in range(
        first_row,
        MAX_ROWS
    ):

        y1 = int(round(
            ROW_START_Y
            +
            row * ROW_HEIGHT
        ))

        y2 = int(round(
            y1
            +
            ROW_HEIGHT
            -
            1
        ))

        for field, column_box in (
            COLUMNS.items()
        ):

            x1 = int(column_box[0])
            x2 = int(column_box[2])

            box = (
                x1,
                y1,
                x2,
                y2
            )

            # Tables use strictly 0 padding so they don't capture adjacent grid lines
            recognition = recognize_region(
                recognizer,
                image,
                box,
                padding_x=0,
                padding_y=0
            )

            if recognition.text or recognition.confidence >= 0.20:

                item = {
                    "page": page_number,
                    "field": field,
                    "row": row,
                    "text": recognition.text,
                    "confidence": recognition.confidence,
                    "box": list(box),
                }

                results.append(item)

                if field_review_needed(field, recognition.text, recognition.confidence):
                    review_items.append(item)

            completed_jobs += 1

            if progress_callback:
                progress_callback(
                    completed_jobs,
                    total_jobs,
                    f"Reading row {row + 1}: {field}"
                )

    return (
        results,
        review_items
    )