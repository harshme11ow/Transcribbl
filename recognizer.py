from dataclasses import dataclass
import os
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


@dataclass
class RecognitionResult:
    text: str
    confidence: float


class LocalHandwritingRecognizer:
    def __init__(self, model_name="microsoft/trocr-base-handwritten"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def recognize(self, gray_image):
        """Return transcription and an initial token-probability confidence score."""
        image = Image.fromarray(gray_image).convert("RGB")
        pixel_values = self.processor(
            images=image, return_tensors="pt"
        ).pixel_values.to(self.device)

        output = self.model.generate(
            pixel_values,
            max_new_tokens=128,
            return_dict_in_generate=True,
            output_scores=True,
        )

        text = self.processor.batch_decode(
            output.sequences, skip_special_tokens=True
        )[0].strip()

        # Mean maximum token probability. Useful as a review signal but not a
        # statistically calibrated probability of correctness.
        if output.scores:
            token_confidences = [
                torch.softmax(score[0], dim=-1).max().item()
                for score in output.scores
            ]
            confidence = float(sum(token_confidences) / len(token_confidences))
        else:
            confidence = 0.0

        return RecognitionResult(text=text, confidence=confidence)
