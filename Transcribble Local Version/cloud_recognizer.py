import google.generativeai as genai
from pydantic import BaseModel, Field
import json

# Replace with your actual API key

class TableRow(BaseModel):
    floor: str = Field(description="Floor number or identifier. Blank string if empty.")
    space: str = Field(description="Tenant or space name. Blank string if empty.")
    light_fc: str = Field(description="Light reading in fc. Blank string if empty.")
    temp_f: str = Field(description="Temperature reading in deg F. Blank string if empty.")
    rh_pct: str = Field(description="Relative humidity reading in %. Blank string if empty.")
    time: str = Field(description="Time of reading. Blank string if empty.")
    co2_ppm: str = Field(description="CO2 reading in ppm. Blank string if empty.")
    voc_ug_m3: str = Field(description="VOC reading. Blank string if empty.")
    comments: str = Field(description="Row comments. Blank string if empty.")

class FormExtraction(BaseModel):
    building_name: str = Field(description="Building Name header. Blank string if empty.")
    completed_by: str = Field(description="Completed By header. Blank string if empty.")
    date: str = Field(description="Date header. Blank string if empty.")
    building_escort: str = Field(description="Building Escort header. Blank string if empty.")
    co2_meter_number: str = Field(description="CO2 Meter Number header. Blank string if empty.")
    general_notes: str = Field(description="Any floating handwritten margin notes outside the table (e.g. signage observations).")
    table_data: list[TableRow] = Field(description="List of table rows.")

class CloudFormRecognizer:
    def __init__(self):
        # Hardcoding the explicitly required 3.6-flash model
        selected_model_name = "gemini-3.6-flash"
        
        print(f"Using Cloud Vision model: {selected_model_name}")
        self.model = genai.GenerativeModel(selected_model_name)

    def process_document(self, img):
        prompt = (
            "You are an expert environmental document parser. Analyze this site visit form. "
            "1. Extract header fields (Building Name, Completed By, Date, Building Escort, CO2 Meter #).\n"
            "2. Extract each table row with exact cell values across the columns.\n"
            "3. Capture any floating handwritten notes or checklist marks in general_notes.\n"
            "Return exact handwritten values faithfully."
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