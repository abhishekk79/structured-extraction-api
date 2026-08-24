import os
import instructor
from dotenv import load_dotenv
from openai import OpenAI

from models import JobPosting

load_dotenv()

raw_client = OpenAI(
    base_url=os.environ["NVIDIA_BASE_URL"],
    api_key=os.environ["NVIDIA_API_KEY"],
)

client = instructor.from_openai(raw_client)

with open("sample_job_posting.txt") as f:
    job_posting_text = f.read()

result: JobPosting = client.chat.completions.create(
    model=os.environ["NVIDIA_MODEL"],
    response_model=JobPosting,
    messages=[
        {
            "role": "user",
            "content": f"Extract the job details from this posting:\n\n{job_posting_text}",
        }
    ],
    temperature=0,
    max_tokens=500,
)

print(result.model_dump_json(indent=2))
