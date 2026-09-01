# -----------------------------
# CANONICAL PAGE SIZE
# -----------------------------
#
# IMPORTANT: This form is a LANDSCAPE-oriented Letter page
# (792 x 612 pt), not portrait. At the 2x zoom used in
# main.py / worker.py (pymupdf.Matrix(2, 2)), a 792x612pt
# page renders to 1584x1224 pixels (144 DPI).
#
# All coordinates below were measured directly on that
# 1584x1224 render. If you ever change the zoom factor in
# main.py/worker.py, these numbers (and the ones below)
# must be rescaled accordingly.

CANONICAL_WIDTH = 1584
CANONICAL_HEIGHT = 1224


# -----------------------------
# HEADER HANDWRITING FIELDS
# -----------------------------
# Each box sits just above the printed underline for that
# field, wide enough to catch the full handwritten answer.

HEADER_FIELDS = {
    "building_name": (255, 117, 670, 151),
    "completed_by": (255, 152, 670, 186),
    "date": (255, 185, 670, 219),
    "building_escort": (255, 219, 725, 253),
    "co2_meter_number": (255, 249, 670, 283),
}


# -----------------------------
# TABLE COLUMNS
# -----------------------------
# x-boundaries measured from the table's vertical grid
# lines. Only x1/x2 from each tuple are actually used for
# columns; y1/y2 here are placeholders (extract.py builds
# the real y-range per-row from ROW_START_Y / ROW_HEIGHT).

COLUMNS = {
    "floor": (141, 363, 258, 1099),
    "space": (258, 363, 471, 1099),
    "light_fc": (471, 363, 568, 1099),
    "temp_f": (568, 363, 665, 1099),
    "rh_pct": (665, 363, 763, 1099),
    "time": (763, 363, 861, 1099),
    "co2_ppm": (861, 363, 963, 1099),
    "voc_ug_m3": (963, 363, 1069, 1099),
    "comments": (1069, 363, 1496, 1099),
}


# -----------------------------
# ROW INFORMATION
# -----------------------------
# The table has exactly 22 data rows (the printed "Outside
# Air" row plus 21 blank rows below it), running from the
# bottom of the sub-header row (y=363) to the table's
# bottom border (y=1099). That's (1099 - 363) / 22 = 33.45px
# per row - kept as a float and rounded when building each
# crop box (see extract.py) to avoid cumulative drift by
# the last row.

ROW_START_Y = 363
ROW_HEIGHT = 33.45
MAX_ROWS = 22

SKIP_FIRST_DATA_ROW = False


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