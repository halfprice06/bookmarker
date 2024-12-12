import instructor
from pydantic import BaseModel
from typing import List
from anthropic import Anthropic
import base64

class DocumentMetadata(BaseModel):
    title: str
    date: str
    summary: str
    tags: List[str]

class InstructorClient:
    def __init__(self, anthropic_client: Anthropic):
        self.client = instructor.from_anthropic(anthropic_client)
    
    def extract_metadata(self, pages_images_b64: list[str]) -> DocumentMetadata:
        # We provide a system prompt and user data:
        # We'll send all pages as images plus instructions
        messages = [
            {
                "role": "user",
                "content": [
                    {"type":"text","text":"Extract the following information from the given document:\n1. Document Title (use a short but descriptive title)\n2. The date the document was created, or in the case of legal pleadings, the date the document was originally filed. in the format YYYY-MM-DD. If you cannot tell, enter the date as Unknown.\n3. Document Summary\n4. Document Tags - Use the Type of Tags You'd Expect An Attorney to Assign in a Document Review Project\n"},
                ] + [
                    {"type":"image", "source":{"type":"base64", "media_type":"image/png","data":img_b64}}
                    for img_b64 in pages_images_b64
                ]
            }
        ]
        resp = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=8000,
            messages=messages,
            response_model=DocumentMetadata,
        )
        return resp
