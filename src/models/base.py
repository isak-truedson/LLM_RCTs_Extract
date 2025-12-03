from abc import ABC, abstractmethod
import os

class BaseModel(ABC):
    def __init__(self, model_name):
        self.model_name = model_name

    @abstractmethod
    def generate(self, pdf_path, prompt_text, few_shot_examples=None):
        """
        Generate extraction from a PDF.

        Args:
            pdf_path (Path): Path to the target PDF.
            prompt_text (str): The instructions and ICO list.
            few_shot_examples (list): List of (pdf_path, label_content) tuples.

        Returns:
            str: The raw JSON output from the model.
        """
        pass
