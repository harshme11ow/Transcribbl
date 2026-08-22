# Transcribbl.


# Local Environmental Form Transcriber

This starter project is designed for the standardized landscape LEED site-visit form you uploaded.

## What this version does

1. Converts PDF pages or images into images.
2. Detects and straightens the page.
3. Warps the page to a fixed canonical layout.
4. Crops known form fields using fixed coordinates.
5. Runs a **local handwriting recognition model** (TrOCR) on handwritten regions.
6. Computes an initial confidence score from model token probabilities.
7. Exports recognized data to Excel.
8. Highlights low-confidence cells for manual review.
9. Saves review metadata, including page, field, row, and confidence.

No image or text needs to be sent to a cloud API.

## Important

The first run of Hugging Face TrOCR normally downloads model weights from the internet.
For a truly air-gapped deployment, download/cache the model weights once on an approved machine and run with `HF_HUB_OFFLINE=1`.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --input "sample.pdf" --output "output.xlsx"
```

## Current form structure

The code is built around the uploaded form's fixed layout:

- Building Name
- Completed By
- Date
- Building Escort
- CO2 Meter #
- Floor
- Space
- Light (fc)
- Temp (°F)
- RH (%)
- Time
- CO2 (ppm)
- VOC (µg/m3)
- Comments

The crop coordinates are intentionally isolated in `form_layout.py` so they can be refined after testing on real handwritten scans.

## Recommended next step

Collect 20-50 representative completed forms from multiple handwriting styles and use them only for testing the pipeline first. Then refine:
- perspective correction
- field coordinates
- handwriting preprocessing
- confidence thresholds
- domain vocabulary
- Excel mapping

Do not train or fine-tune until you have a clean baseline measurement.
