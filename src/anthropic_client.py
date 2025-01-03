import os
import base64
import time
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT, APIError, RateLimitError

class AnthropicClient:
    def __init__(self, api_key=None, max_retries=3, retry_delay=1):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def call_model(self, model: str, messages: list, system: str, max_tokens=8000, temperature=0):
        retries = 0
        while retries < self.max_retries:
            try:
                return self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                    temperature=temperature,
                )
            except RateLimitError as e:
                retries += 1
                if retries == self.max_retries:
                    raise Exception(f"Rate limit exceeded after {retries} retries") from e
                print(f"Rate limit hit, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay * (2 ** (retries - 1)))  # Exponential backoff
            except APIError as e:
                retries += 1
                if retries == self.max_retries:
                    raise Exception(f"API error after {retries} retries: {str(e)}") from e
                print(f"API error occurred, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
            except Exception as e:
                raise Exception(f"Unexpected error during API call: {str(e)}") from e

    def is_new_document(self, prev_image_b64: str, curr_image_b64: str) -> bool:
        try:
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
        except (RateLimitError, APIError) as e:
            # Let these propagate up since call_model already handles retries
            raise
        except Exception as e:
            # Handle any other unexpected errors (like malformed responses, etc)
            print(f"Unexpected error in is_new_document: {str(e)}")
            # Default to treating it as not a new document in case of errors
            # This is safer than potentially splitting documents incorrectly
            return False
