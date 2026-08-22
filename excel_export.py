from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.comments import Comment
from form_layout import MANUAL_REVIEW_THRESHOLD

YELLOW = PatternFill(fill_type="solid", fgColor="FFF2CC")
GRAY = PatternFill(fill_type="solid", fgColor="D9EAD3")
THIN = Side(style="thin", color="777777")

COLUMN_ORDER = [
    "floor", "space", "light_fc", "temp_f", "rh_pct",
    "time", "co2_ppm", "voc_ug_m3", "comments"
]

HEADERS = {
    "floor": "Floor",
    "space": "Space",
    "light_fc": "Light (fc)",
    "temp_f": "Temp (°F)",
    "rh_pct": "RH (%)",
    "time": "Time",
    "co2_ppm": "CO2 (ppm)",
    "voc_ug_m3": "VOC (µg/m3)",
    "comments": "COMMENTS",
}


def build_workbook(results, output_path, template_path=None):
    wb = load_workbook(template_path) if template_path else Workbook()
    ws = wb.active
    ws.title = "Transcribed Form"

    # If this is not a supplied Excel template, create a matching data layout.
    if template_path is None:
        ws["A1"] = "Building Name:"
        ws["A2"] = "Completed By:"
        ws["A3"] = "Date:"
        ws["A4"] = "Building Escort:"
        ws["A5"] = "CO2 Meter #:"

        for idx, field in enumerate(COLUMN_ORDER, start=1):
            cell = ws.cell(row=7, column=idx, value=HEADERS[field])
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
            cell.border = Border(
                left=THIN, right=THIN, top=THIN, bottom=THIN
            )

    header_map = {
        "building_name": "B1",
        "completed_by": "B2",
        "date": "B3",
        "building_escort": "B4",
        "co2_meter_number": "B5",
    }

    row_data = {}
    for item in results:
        field = item["field"]
        if item["row"] is None and field in header_map:
            ws[header_map[field]] = item["text"]
            if item["confidence"] < MANUAL_REVIEW_THRESHOLD:
                ws[header_map[field]].fill = YELLOW
                ws[header_map[field]].comment = Comment(
                    f"Low confidence: {item['confidence']:.1%}",
                    "Local Form Transcriber"
                )
        elif item["row"] is not None:
            row_data.setdefault(item["row"], {})[field] = item

    start_excel_row = 8
    for source_row, fields in sorted(row_data.items()):
        excel_row = start_excel_row + source_row
        for col_idx, field in enumerate(COLUMN_ORDER, start=1):
            item = fields.get(field)
            if not item:
                continue
            cell = ws.cell(
                row=excel_row, column=col_idx, value=item["text"]
            )
            cell.border = Border(
                left=THIN, right=THIN, top=THIN, bottom=THIN
            )
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            if item["confidence"] < MANUAL_REVIEW_THRESHOLD:
                cell.fill = YELLOW
                cell.comment = Comment(
                    f"Low confidence: {item['confidence']:.1%}; "
                    f"page {item['page']}, source row {source_row}",
                    "Local Form Transcriber"
                )

    wb.save(output_path)


def write_review_sheet(output_path, review_items):
    wb = load_workbook(output_path)
    ws = wb.create_sheet("Manual Review")

    ws.append(["Page", "Field", "Source Row", "Recognized Text", "Confidence", "Action"])
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for item in review_items:
        ws.append([
            item["page"],
            item["field"],
            item["row"],
            item["text"],
            item["confidence"],
            "REVIEW",
        ])

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if row[5].value == "REVIEW":
                cell.fill = YELLOW

    wb.save(output_path)
