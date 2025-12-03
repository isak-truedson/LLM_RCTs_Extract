import os
import base64
from .base import BaseModel
from openai import OpenAI
import pymupdf  # PyMuPDF

class GPTModel(BaseModel):
    def __init__(self, model_name="gpt-4o"):
        super().__init__(model_name)
        # Assumes OPENAI_API_KEY is set in environment
        self.client = OpenAI()

    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF for models that don't support direct PDF upload."""
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            return f"[Error extracting text: {e}]"

    def generate(self, pdf_path, prompt_text, few_shot_examples=None):
        messages = []

        # Handle Few-Shot Examples
        if few_shot_examples:
            for ex_pdf, ex_label in few_shot_examples:
                # Extract text for few-shot PDF
                ex_text = self._extract_text_from_pdf(ex_pdf)

                messages.append({
                    "role": "user",
                    "content": f"[Example Document Content]\n{ex_text}\n\nExtract data..."
                })
                messages.append({
                    "role": "assistant",
                    "content": str(ex_label)
                })

        # Target PDF
        # Since standard OpenAI Chat Completions don't support PDF upload directly,
        # we extract text and pass it.
        target_text = self._extract_text_from_pdf(pdf_path)

        messages.append({
            "role": "user",
            "content": f"[Target Document Content]\n{target_text}\n\n{prompt_text}"
        })

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
