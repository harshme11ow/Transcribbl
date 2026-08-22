import argparse
from pathlib import Path
import json
import cv2
import fitz # Fixed import (previously pymupdf)
import numpy as np

from preprocess import deskew_and_warp
from recognizer import LocalHandwritingRecognizer
from extract import extract_page
from excel_export import build_workbook # Removed write_review_sheet


def load_pages(path):
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        document = fitz.open(path)
        pages = []
        for page in document:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            array = np.frombuffer(pix.samples, dtype=np.uint8)
            image = array.reshape(pix.height, pix.width, 3)
            # PyMuPDF output is RGB; OpenCV expects BGR.
            pages.append(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        return pages

    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not open {path}")
    return [image]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Scanned PDF or image")
    parser.add_argument("--output", default="transcribed_form.xlsx")
    parser.add_argument(
        "--template",
        default=None,
        help="Optional original .xlsx template to preserve existing formatting"
    )
    parser.add_argument(
        "--save-debug",
        action="store_true",
        help="Save aligned page images for troubleshooting"
    )
    args = parser.parse_args()

    recognizer = LocalHandwritingRecognizer()
    all_results = []
    all_review_items = []

    for page_number, page in enumerate(load_pages(args.input), start=1):
        aligned = deskew_and_warp(page)

        if args.save_debug:
            cv2.imwrite(f"debug_aligned_page_{page_number}.png", aligned)

        results, review_items = extract_page(
            aligned, recognizer, page_number=page_number
        )
        all_results.extend(results)
        all_review_items.extend(review_items)

    build_workbook(
        all_results,
        args.output,
        template_path=args.template
    )
# write_review_sheet call removed from here

    json_path = Path(args.output).with_suffix(".json")
    json_path.write_text(json.dumps({
        "results": all_results,
        "manual_review": all_review_items,
    }, indent=2), encoding="utf-8")

    print(f"Created: {args.output}")
    print(f"Created: {json_path}")
    print(f"Manual review items: {len(all_review_items)}")


if __name__ == "__main__":
    main()