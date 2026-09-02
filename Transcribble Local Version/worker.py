from pathlib import Path
import json
import traceback
import cv2
import pymupdf
import numpy as np
from PIL import Image

from PySide6.QtCore import (
    QThread,
    Signal,
)

from florence_recognizer import FlorenceRecognizer
from excel_export import build_workbook


class TranscriptionWorker(QThread):
    progress = Signal(int, str)
    status = Signal(str)
    preview_ready = Signal(object)
    pages_ready = Signal(object)
    completed = Signal(object, object, str)
    failed = Signal(str)

    def __init__(self, input_path, output_path, template_path=None):
        super().__init__()
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.template_path = template_path

    def load_pages(self):
        suffix = self.input_path.suffix.lower()
        if suffix == ".pdf":
            document = pymupdf.open(self.input_path)
            pages = []
            for page in document:
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                array = np.frombuffer(pixmap.samples, dtype=np.uint8)
                rgb = array.reshape(pixmap.height, pixmap.width, 3)
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                pages.append(bgr)
            return pages

        image = cv2.imread(str(self.input_path))
        if image is None:
            raise ValueError("Could not open input file.")
        return [image]

    def run(self):
        try:
            self.progress.emit(5, "Loading form")
            pages = self.load_pages()

            if not pages:
                raise ValueError("No pages found in document.")

            first_page_bgr = pages[0]
            self.preview_ready.emit(first_page_bgr)
            self.pages_ready.emit(pages)

            self.progress.emit(15, "Loading Florence-2 into VRAM...")
            self.status.emit("Initializing local model...")

            recognizer = FlorenceRecognizer()

            first_page_rgb = cv2.cvtColor(first_page_bgr, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(first_page_rgb)

            self.progress.emit(40, "Running dense layout OCR locally...")
            extracted_data = recognizer.process_document(pil_image)

            self.progress.emit(85, "Mapping detections to spreadsheet rows...")

            all_results = []
            all_review_items = []

            header_keys = [
                "building_name", "completed_by", "date", 
                "building_escort", "co2_meter_number"
            ]

            for key in header_keys:
                all_results.append({
                    "page": 1,
                    "field": key,
                    "row": None,
                    "text": extracted_data.get(key, ""),
                    "confidence": 0.99,
                })

            for row_idx, row_dict in enumerate(extracted_data.get("table_data", [])):
                for field, text in row_dict.items():
                    if text and str(text).strip():
                        all_results.append({
                            "page": 1,
                            "field": field,
                            "row": row_idx,
                            "text": str(text),
                            "confidence": 0.99,
                        })

            self.progress.emit(92, "Creating Excel workbook...")
            build_workbook(
                all_results,
                self.output_path,
                template_path=self.template_path
            )

            self.progress.emit(96, "Saving JSON metadata...")
            json_path = self.output_path.with_suffix(".json")
            json_output = {
                "structured_api_data": extracted_data,
                "excel_mapped_results": all_results,
            }
            json_path.write_text(json.dumps(json_output, indent=2), encoding="utf-8")

            self.progress.emit(100, "Complete")
            self.status.emit("Offline transcription complete")
            self.completed.emit(all_results, all_review_items, str(self.output_path))

        except PermissionError:
            self.failed.emit(
                f"Cannot save the Excel file because it is open.\n\n"
                f"Please close '{self.output_path.name}' in Excel and try again."
            )
        except Exception as error:
            full_error = traceback.format_exc()
            print("\n" + "=" * 70)
            print("TRANSCRIPTION ERROR")
            print("=" * 70)
            print(full_error)
            print("=" * 70 + "\n")

            msg = str(error) if str(error).strip() else f"{type(error).__name__}: {repr(error)}"
            self.failed.emit(f"{msg}\n\nFull traceback:\n{full_error}")