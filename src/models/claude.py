import os
import base64
from .base import BaseModel
import anthropic

class ClaudeModel(BaseModel):
    def __init__(self, model_name="claude-3-opus-20240229"): # Placeholder for "Claude Opus 4.5"
        super().__init__(model_name)
        self.client = anthropic.Anthropic()

    def generate(self, pdf_path, prompt_text, few_shot_examples=None):
        messages = []

        # Few-shot examples
        if few_shot_examples:
            for ex_pdf, ex_label in few_shot_examples:
                with open(ex_pdf, "rb") as f:
                    pdf_data = base64.b64encode(f.read()).decode("utf-8")

                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract the data." # Simplified prompt for examples
                        }
                    ]
                })
                messages.append({
                    "role": "assistant",
                    "content": str(ex_label) # JSON string
                })

        # Target PDF
        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt_text
                }
            ]
        })

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"
