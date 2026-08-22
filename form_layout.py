CANONICAL_WIDTH = 1584
CANONICAL_HEIGHT = 1224


# -----------------------------
# HEADER HANDWRITING FIELDS
# -----------------------------

HEADER_FIELDS = {
    "building_name": (205, 118, 665, 145),
    "completed_by": (205, 177, 665, 205),
    "date": (205, 237, 665, 265),
    "building_escort": (205, 297, 665, 325),
    "co2_meter_number": (205, 357, 665, 385),
}


# -----------------------------
# TABLE COLUMNS
# -----------------------------

COLUMNS = {
    "floor": (97, 379, 204, 1223),
    "space": (205, 379, 402, 1223),
    "light_fc": (403, 379, 490, 1223),
    "temp_f": (491, 379, 580, 1223),
    "rh_pct": (581, 379, 668, 1223),
    "time": (669, 379, 759, 1223),
    "co2_ppm": (760, 379, 854, 1223),
    "voc_ug_m3": (855, 379, 951, 1223),
    "comments": (952, 379, 1347, 1223),
}


# -----------------------------
# ROW INFORMATION
# -----------------------------

ROW_START_Y = 380
ROW_HEIGHT = 31
MAX_ROWS = 27

SKIP_FIRST_DATA_ROW = True


# -----------------------------
# CONFIDENCE
# -----------------------------

MANUAL_REVIEW_THRESHOLD = 0.82
MEDIUM_CONFIDENCE_THRESHOLD = 0.92


NUMERIC_FIELDS = {
    "light_fc",
    "temp_f",
    "rh_pct",
    "co2_ppm",
    "voc_ug_m3",
}