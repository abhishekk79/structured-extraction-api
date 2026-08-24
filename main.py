import instructor
from fastapi import FastAPI
from pydantic import BaseModel

from client import NO_THINKING, NVIDIA_MODEL, get_raw_client
from models import JobPosting

app = FastAPI(title="Structured Extraction API")
client = instructor.from_openai(get_raw_client())


class ExtractRequest(BaseModel):
    text: str


@app.post("/extract", response_model=JobPosting)
def extract(request: ExtractRequest) -> JobPosting:
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
