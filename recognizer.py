from dataclasses import dataclass

import torch
from PIL import Image

from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    AutoImageProcessor,
    RobertaTokenizer,  # We are hardcoding the exact class
)


@dataclass
class RecognitionResult:

    text: str
    confidence: float


class LocalHandwritingRecognizer:

    def __init__(
        self,
        model_name="microsoft/trocr-base-handwritten"
    ):

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(
            f"Loading handwriting model on {self.device}"
        )

# Bypass AutoTokenizer entirely to stop it from hunting for sentencepiece
        tokenizer = RobertaTokenizer.from_pretrained(
            model_name
        )
        
        image_processor = AutoImageProcessor.from_pretrained(
            model_name
        )
        
        self.processor = TrOCRProcessor(
            image_processor=image_processor,
            tokenizer=tokenizer
        )
        
        self.model = (
            VisionEncoderDecoderModel
            .from_pretrained(
                model_name
            )
        )

        self.model.to(
            self.device
        )

        self.model.eval()


    @torch.inference_mode()
    def recognize(
        self,
        gray_image
    ):

        image = Image.fromarray(
            gray_image
        ).convert("RGB")

        pixel_values = (
            self.processor(
                images=image,
                return_tensors="pt"
            )
            .pixel_values
            .to(self.device)
        )

        output = self.model.generate(
            pixel_values,
            max_new_tokens=128,
            return_dict_in_generate=True,
            output_scores=True,
        )

        text = (
            self.processor
            .batch_decode(
                output.sequences,
                skip_special_tokens=True
            )[0]
            .strip()
        )

        # Calculate an initial confidence signal.
        #
        # This is NOT yet a statistically calibrated
        # probability of being correct.
        #
        # Later, we can calibrate it using completed
        # forms with known ground truth.

        if output.scores:

            token_confidences = []

            for score in output.scores:

                probabilities = torch.softmax(
                    score[0],
                    dim=-1
                )

                confidence = (
                    probabilities
                    .max()
                    .item()
                )

                token_confidences.append(
                    confidence
                )

            confidence = (
                sum(token_confidences)
                / len(token_confidences)
            )

        else:

            confidence = 0.0

        return RecognitionResult(
            text=text,
            confidence=float(confidence)
        )