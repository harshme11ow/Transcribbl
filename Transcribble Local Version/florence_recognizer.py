import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image

from form_layout import (
    HEADER_FIELDS,
    COLUMNS,
    ROW_START_Y,
    ROW_HEIGHT,
    MAX_ROWS
)

class FlorenceRecognizer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_id = "microsoft/Florence-2-large"
        
        print(f"Loading {model_id} on {self.device} (downloads ~3GB of weights on first run)...")
        
        self.processor = AutoProcessor.from_pretrained(
            model_id, 
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            trust_remote_code=True
        ).to(self.device).eval()

    @torch.inference_mode()
    def process_document(self, img: Image.Image):
        task = "<OCR_WITH_REGION>"
        
        inputs = self.processor(
            text=task, 
            images=img, 
            return_tensors="pt"
        ).to(self.device)
        
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=2048,
            num_beams=3,
        )
        
        generated_text = self.processor.batch_decode(
            generated_ids, 
            skip_special_tokens=False
        )[0]
        
        parsed = self.processor.post_process_generation(
            generated_text, 
            task=task, 
            image_size=(img.width, img.height)
        )
        
        ocr_results = parsed.get(task, {})
        quad_boxes = ocr_results.get('quad_boxes', [])
        labels = ocr_results.get('labels', [])

        extracted = {k: [] for k in HEADER_FIELDS.keys()}
        table_data = {row: {col: [] for col in COLUMNS.keys()} for row in range(MAX_ROWS)}
        general_notes = []

        def in_box(x, y, box, pad=0):
            return (box[0] - pad <= x <= box[2] + pad) and (box[1] - pad <= y <= box[3] + pad)

        for box, text in zip(quad_boxes, labels):
            cx = sum(box[0::2]) / 4.0
            cy = sum(box[1::2]) / 4.0
            matched = False
            
            # Header check
            for h_key, h_box in HEADER_FIELDS.items():
                if in_box(cx, cy, h_box, pad=15): 
                    extracted[h_key].append(text)
                    matched = True
                    break
                    
            if matched: 
                continue
            
            # Table rows
            if (ROW_START_Y - 10) <= cy <= (ROW_START_Y + (MAX_ROWS * ROW_HEIGHT) + 10):
                row_idx = int((cy - ROW_START_Y) / ROW_HEIGHT)
                row_idx = max(0, min(MAX_ROWS - 1, row_idx)) 
                
                for c_key, c_box in COLUMNS.items():
                    if c_box[0] <= cx <= c_box[2]:
                        table_data[row_idx][c_key].append(text)
                        matched = True
                        break
                        
            if matched: 
                continue
            
            # Margin notes
            ignore_phrases = [
                "inspect", "ventilation", "energy", "meters", "picture", 
                "message", "leed", "pine", "building", "name:", "completed", 
                "date:", "escort", "meter", "floor", "space", "iaq", "light", 
                "temp", "time", "voc", "comments", "tenant", "suite"
            ]
            text_lower = text.lower()
            if not any(p in text_lower for p in ignore_phrases) and len(text) > 1:
                general_notes.append(text)

        final_output = {
            "general_notes": " ".join(general_notes)
        }
        
        for k in HEADER_FIELDS.keys():
            final_output[k] = " ".join(extracted[k])
            
        final_output["table_data"] = []
        for row_idx in range(MAX_ROWS):
            row_dict = {}
            for c_key in COLUMNS.keys():
                row_dict[c_key] = " ".join(table_data[row_idx][c_key])
            final_output["table_data"].append(row_dict)

        return final_output