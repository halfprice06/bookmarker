import os
import base64
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

class AnthropicClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
    
    def call_model(self, model: str, messages: list, system: str, max_tokens=8000, temperature=0):
        # messages is a list of dicts with {role: 'user'/'assistant', content: [...] or string}
        return self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            temperature=temperature,
        )

    def is_new_document(self, prev_image_b64: str, curr_image_b64: str) -> bool:
        # System instruction to ensure consistent logic
        system_prompt = """You are a document segmentation assistant. Given two consecutive pages (previous and current), determine if the current page starts a new document. 
Output only 'YES' or 'NO'.
Consider big structural changes like a new cover page, a new heading, or a drastically different layout as signs of a new doc start."""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Previous page image:"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": prev_image_b64}},
                    {"type": "text", "text": "\nCurrent page image:"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": curr_image_b64}},
                    {"type": "text", "text": "\nDoes the current page start a new document? Respond YES or NO."}
                ]
            }
        ]

        resp = self.call_model(
            model="claude-3-5-sonnet-latest", 
            messages=messages,
            system=system_prompt,
            max_tokens=8000,
            temperature=0
        )
        answer = resp.content[0].text.strip().upper()
        return "YES" in answer
