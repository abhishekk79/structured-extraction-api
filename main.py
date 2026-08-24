import logging

import instructor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from client import NO_THINKING, NVIDIA_MODEL, get_raw_client
from models import JobPosting

logger = logging.getLogger(__name__)

app = FastAPI(title="Structured Extraction API")
client = instructor.from_openai(get_raw_client())


class ExtractRequest(BaseModel):
    text: str = Field(
        min_length=1, description="Free-text job posting to extract structured data from"
    )


@app.post("/extract", response_model=JobPosting)
def extract(request: ExtractRequest) -> JobPosting:
    try:
        return client.chat.completions.create(
            model=NVIDIA_MODEL,
            response_model=JobPosting,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the job details from this posting:\n\n{request.text}",
                }
            ],
            temperature=0,
            max_tokens=1500,
            extra_body=NO_THINKING,
        )
    except Exception:
        logger.exception("Extraction failed")
        raise HTTPException(
            status_code=502,
            detail="Failed to extract structured data from the upstream model.",
        ) from None
