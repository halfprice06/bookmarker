import instructor
from pydantic import BaseModel
from typing import List
import time
from anthropic import Anthropic, APIError, RateLimitError
import base64
from openai import OpenAI

class DocumentMetadata(BaseModel):
    title: str
    date: str
    summary: str
    tags: List[str]

class InstructorClient:
    def __init__(self, model_client, provider="anthropic", max_retries=3, retry_delay=1):
        self.provider = provider
        if provider == "anthropic":
            self.client = instructor.from_anthropic(model_client)
        else:
            self.client = instructor.patch(model_client)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def extract_metadata(self, pages_data: list[tuple[str, str]], page_markdowns: list[str]) -> DocumentMetadata:
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the following information from the given document:\n1. Document Title (use a short but descriptive title)\n2. The date the document was created, or in the case of legal pleadings, the date the document was originally filed, in the format YYYY-MM-DD. If you cannot tell very obviously when the document was created or filed, enter the date as Unknown. Don't guess. Not all dates correspond to the date the document was created or filed, it could just be a date referenced in the document for other reasons.\n3. Document Summary. When you are summarizing the document, keep the following in mind: We represent OxyChem in this proceeding.OxyChem’s interest is ensuring that the cost of these facilities does not get passed on to Entergy’s other customers. OxyChem has 3 large plants in Louisiana, one of which has a CCGT that provides all of its power and the other two of which take all their power from Entergy. OxyChem also has a long-term Purchased Power Agreement (PPA) through which it supplies Entergy with excess power from its CCGT. So, OxyChem may contest whether Entergy should have put the power supply for this new customer out for solicitation through an RFP into which OxyChem could have bid.\n4. Document Tags - Use the Type of Tags You'd Expect An Attorney to Assign in a Document Review Project\n"},
                        ] + [
                            item for idx, ((page_b64, _), page_markdown) in enumerate(zip(pages_data, page_markdowns)) for item in [
                                {"type": "image_url" if self.provider == "openai" else "image",
                                 "image_url" if self.provider == "openai" else "source": {
                                     "url" if self.provider == "openai" else "type": f"data:image/png;base64,{page_b64}" if self.provider == "openai" else "base64",
                                     "detail": "high" if self.provider == "openai" else None,
                                     "media_type": "image/png" if self.provider == "anthropic" else None,
                                     "data": page_b64 if self.provider == "anthropic" else None
                                 }},
                                {"type": "text", "text": f"Page {idx+1} formatted content:\n{page_markdown}\n---"}
                            ]
                        ]
                    }
                ]
                
                model = "claude-3-5-sonnet-latest" if self.provider == "anthropic" else "gpt-4o"
                return self.client.chat.completions.create(
                    model=model,
                    max_tokens=8000,
                    messages=messages,
                    response_model=DocumentMetadata,
                )
            except RateLimitError as e:
                retries += 1
                last_error = e
                if retries == self.max_retries:
                    break
                print(f"Rate limit hit, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay * (2 ** (retries - 1)))  # Exponential backoff
            except APIError as e:
                retries += 1
                last_error = e
                if retries == self.max_retries:
                    break
                print(f"API error occurred, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
            except Exception as e:
                # For unexpected errors, fail immediately
                raise Exception(f"Unexpected error during metadata extraction: {str(e)}") from e
        
        # If we've exhausted retries, raise the last error
        if last_error:
            if isinstance(last_error, RateLimitError):
                raise Exception(f"Rate limit exceeded after {retries} retries") from last_error
            else:
                raise Exception(f"API error after {retries} retries: {str(last_error)}") from last_error
