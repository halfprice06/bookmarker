import os
import time
from openai import OpenAI
from typing import List

class OpenAIClient:
    def __init__(self, api_key=None, max_retries=3, retry_delay=1):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def call_model(self, model: str, messages: list, system: str, max_tokens=8000, temperature=0):
        retries = 0
        while retries < self.max_retries:
            try:
                # Convert messages to OpenAI format
                formatted_messages = []
                if system:
                    formatted_messages.append({"role": "system", "content": system})
                
                for msg in messages:
                    formatted_content = []
                    for item in msg["content"]:
                        if item["type"] == "text":
                            formatted_content.append({
                                "type": "text",
                                "text": item["text"]
                            })
                        elif item["type"] == "image":
                            formatted_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{item['source']['data']}",
                                    "detail": "high"
                                }
                            })
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": formatted_content
                    })

                response = self.client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                
                # Convert OpenAI response to Anthropic-like format for compatibility
                return type('Response', (), {
                    'content': [
                        type('Content', (), {'text': response.choices[0].message.content})()
                    ]
                })()
                
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    raise Exception(f"API error after {retries} retries: {str(e)}") from e
                print(f"API error occurred, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay * (2 ** (retries - 1)))  # Exponential backoff

    def is_new_document(self, prev_image_b64: str, curr_image_b64: str) -> bool:
        try:
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
                model="gpt-4o-mini", 
                messages=messages,
                system=system_prompt,
                max_tokens=8000,
                temperature=0
            )
            answer = resp.content[0].text.strip().upper()
            return "YES" in answer
        except Exception as e:
            print(f"Unexpected error in is_new_document: {str(e)}")
            return False 