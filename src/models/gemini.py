import os
import time
from .base import BaseModel
import google.genai

class GeminiModel(BaseModel):
    def __init__(self, model_name="gemini-1.5-pro-latest"): # Placeholder for "Gemini 3 Pro"
        super().__init__(model_name)
        # Assumes GOOGLE_API_KEY is set
        self.client = google.genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    def generate(self, pdf_path, prompt_text, few_shot_examples=None):
        # Gemini handles files by uploading them first

        contents = []

        # Few-shot examples
        if few_shot_examples:
            for ex_pdf, ex_label in few_shot_examples:
                # Upload file
                # Note: In a production loop, we should cache these uploads or delete them.
                # Here we upload fresh for simplicity, but it might be slow.
                try:
                    file_ref = self.client.files.upload(file=ex_pdf)

                    # Wait for processing? Usually needed for video, PDF might be fast.
                    # Simple check loop could be added here.

                    contents.append(file_ref)
                    contents.append("Extract data.") # User turn
                    contents.append(str(ex_label))   # Model turn (simulated history?)
                    # Gemini generate_content doesn't take 'history' list like Chat.
                    # It takes a list of contents.
                    # BUT mixing files and text in a single list acts as one prompt.
                    # To do few-shot history, we might need `start_chat` or structure it carefully.
                    # The `contents` arg in `generate_content` is usually the "current" prompt parts.
                    # To do history, we usually use `chat = model.start_chat(history=...)`.

                    # Let's switch to chat mode for few-shot to be safe.
                    pass
                except Exception as e:
                    print(f"Failed to upload example {ex_pdf}: {e}")

        # If we have few-shot, we might need a ChatSession.
        # But 'generate_content' can take a sequence of (User, Model, User) parts if formatted right,
        # or we just shove everything into context if the API allows.
        # However, for Gemini, the easiest "Stateless" few-shot with files is:
        # [File1, "Output: {...}", File2, "Output: {...}", TargetFile, "Prompt"]
        # But `generate_content` usually treats the list as ONE user message.
        # To distinguish turns, we need the `contents` to be a list of Content objects with roles.

        # We will use the proper `types.Content` structure if needed, or `client.chats.create`.
        # For simplicity and robustness with the new `google-genai` SDK (v1.0+):

        chat_history = []
        if few_shot_examples:
            for ex_pdf, ex_label in few_shot_examples:
                # Upload
                with open(ex_pdf, "rb") as f:
                    file_content = self.client.files.upload(file=f, config={'display_name': ex_pdf.name})

                # Check state
                while file_content.state.name == "PROCESSING":
                    time.sleep(1)
                    file_content = self.client.files.get(name=file_content.name)

                chat_history.append(
                    {"role": "user", "parts": [file_content, "Extract data."]}
                )
                chat_history.append(
                    {"role": "model", "parts": [str(ex_label)]}
                )

        # Target PDF
        with open(pdf_path, "rb") as f:
            target_file = self.client.files.upload(file=f, config={'display_name': pdf_path.name})

        while target_file.state.name == "PROCESSING":
            time.sleep(1)
            target_file = self.client.files.get(name=target_file.name)

        # Generate
        # We can use chat.send_message
        chat = self.client.chats.create(model=self.model_name, history=chat_history)

        try:
            response = chat.send_message(
                message=[target_file, prompt_text]
            )
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
