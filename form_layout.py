# Canonical page dimensions used by this starter.
# The uploaded PDF is US Letter landscape, rendered here at 2x.
CANONICAL_WIDTH = 1584
CANONICAL_HEIGHT = 1224

# Coordinates are x1, y1, x2, y2 in canonical pixels.
# These are initial estimates based on the provided blank template.
HEADER_FIELDS = {
    "building_name": (205, 118, 665, 145),
    "completed_by":  (205, 177, 665, 205),
    "date":          (205, 237, 665, 265),
    "building_escort": (205, 297, 665, 325),
    "co2_meter_number": (205, 357, 665, 385),
}

# Data columns for handwritten values.
# The header occupies roughly y=316-379 in the rendered page.
COLUMNS = {
    "floor":    (97, 379, 204, 1223),
    "space":    (205, 379, 402, 1223),
    "light_fc": (403, 379, 490, 1223),
    "temp_f":   (491, 379, 580, 1223),
    "rh_pct":   (581, 379, 668, 1223),
    "time":     (669, 379, 759, 1223),
    "co2_ppm":  (760, 379, 854, 1223),
    "voc_ug_m3": (855, 379, 951, 1223),
    "comments": (952, 379, 1347, 1223),
}

# Approximate first data row and row height from the supplied blank form.
ROW_START_Y = 380
ROW_HEIGHT = 31
MAX_ROWS = 27

# The first row contains the preprinted "Outside Air" text and should not be
# interpreted as handwriting by default.
SKIP_FIRST_DATA_ROW = True

NUMERIC_FIELDS = {"light_fc", "temp_f", "rh_pct", "co2_ppm", "voc_ug_m3"}

# Initial review threshold. This should be calibrated using real labeled forms.
MANUAL_REVIEW_THRESHOLD = 0.82
