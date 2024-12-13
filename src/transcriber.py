from typing import List, Tuple
import instructor
from anthropic import Anthropic
from pydantic import BaseModel
from openai import OpenAI
import os
from pathlib import Path

class PageTranscription(BaseModel):
    markdown_text: str

class DocumentTranscriber:
    def __init__(self, model_client, provider="anthropic"):
        self.provider = provider
        if provider == "anthropic":
            self.client = instructor.from_anthropic(model_client)
        else:
            self.client = instructor.patch(model_client)

    def transcribe_page(self, image_b64: str, extracted_text: str) -> str:
        """Transcribe a single page to markdown format."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Please transcribe this document page exactly as it appears, preserving all formatting. 
                            Format your response as markdown, including:
                            - Proper headings (# for main titles, ## for subtitles, etc.)
                            - Bold and italic text where appropriate
                            - Lists (numbered and bulleted) as they appear
                            - Indentation and spacing
                            - Tables if present
                            
                            I'm providing both the image and OCR-extracted text to help with accuracy.
                            Focus on creating a precise markdown representation of the document's layout and styling."""
                        },
                        {
                            "type": "image_url" if self.provider == "openai" else "image",
                            "image_url" if self.provider == "openai" else "source": {
                                "url" if self.provider == "openai" else "type": f"data:image/png;base64,{image_b64}" if self.provider == "openai" else "base64",
                                "detail": "high" if self.provider == "openai" else None,
                                "media_type": "image/png" if self.provider == "anthropic" else None,
                                "data": image_b64 if self.provider == "anthropic" else None
                            }
                        },
                        {
                            "type": "text",
                            "text": f"OCR-extracted text for reference:\n{extracted_text}"
                        }
                    ]
                }
            ]
            
            model = "claude-3-5-sonnet-latest" if self.provider == "anthropic" else "gpt-4o-mini"
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=8000,
                messages=messages,
                response_model=PageTranscription
            )
            return response.markdown_text
        except Exception as e:
            print(f"Error transcribing page: {str(e)}")
            return ""

    def transcribe_document(self, pages_data: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
        """Transcribe all pages of a document and return both combined and individual transcriptions."""
        print("Starting markdown transcription...")
        transcriptions = []
        
        for i, (image_b64, extracted_text) in enumerate(pages_data):
            print(f"Transcribing page {i+1}/{len(pages_data)}...")
            page_transcription = self.transcribe_page(image_b64, extracted_text)
            transcriptions.append(page_transcription)
            
        # Combine all pages with clear page markers
        full_transcription = ""
        for i, page_markdown in enumerate(transcriptions, 1):
            if i > 1:  # Add extra newline before page markers (except first page)
                full_transcription += "\n\n"
            
            full_transcription += f"--- PDF PAGE {i} ---\n\n"
            full_transcription += page_markdown.strip()
            full_transcription += f"\n\n--- END OF PDF PAGE {i} ---"
        
        print("Transcription complete")
        return full_transcription, transcriptions

    @staticmethod
    def ensure_dir_exists(file_path: str) -> None:
        """Ensure that the directory for the given file path exists."""
        directory = os.path.dirname(file_path)
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True) 