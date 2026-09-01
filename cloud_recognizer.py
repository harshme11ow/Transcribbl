import google.generativeai as genai
from pydantic import BaseModel, Field
import PIL.Image
import json

# Replace with your actual API key
genai.configure(api_key="YOUR_API_KEY")

class TableRow(BaseModel):
    floor: str = Field(description="Floor number or name. Leave blank if empty.")
    space: str = Field(description="Tenant or space name. Leave blank if empty.")
    light_fc: str = Field(description="Light reading. Leave blank if empty.")
    temp_f: str = Field(description="Temperature reading. Leave blank if empty.")
    rh_pct: str = Field(description="Relative humidity reading. Leave blank if empty.")
    time: str = Field(description="Time of reading. Leave blank if empty.")
    co2_ppm: str = Field(description="CO2 reading. Leave blank if empty.")
    voc_ug_m3: str = Field(description="VOC reading. Leave blank if empty.")
    comments: str = Field(description="Row-specific comments. Leave blank if empty.")

class FormExtraction(BaseModel):
    building_name: str
    completed_by: str
    date: str
    building_escort: str
    co2_meter_number: str
    general_notes: str = Field(description="Any floating handwriting or margin notes outside the main table (e.g., notes about signage).")
    table_data: list[TableRow]

class CloudFormRecognizer:
    def __init__(self):
        # Gemini 1.5 Flash is highly optimized for fast, cheap document OCR
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def process_document(self, image_path):
        """
        Takes the full, uncropped image and extracts all data into a structured format.
        """
        img = PIL.Image.open(image_path)
        
        prompt = (
            "Analyze this site visit form. Extract the header fields, read the table data "
            "row by row, and capture any free-floating handwritten notes in the margins. "
            "Return the exact handwritten text."
        )

        response = self.model.generate_content(
            [prompt, img],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=FormExtraction,
                temperature=0.1
            ),
        )

        return json.loads(response.text)