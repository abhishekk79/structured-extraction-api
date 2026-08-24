import instructor

from client import NO_THINKING, NVIDIA_MODEL, PROJECT_ROOT, get_raw_client
from models import JobPosting

client = instructor.from_openai(get_raw_client())

with open(PROJECT_ROOT / "sample_job_posting.txt") as f:
    job_posting_text = f.read()

result: JobPosting = client.chat.completions.create(
    model=NVIDIA_MODEL,
    response_model=JobPosting,
    messages=[
        {
            "role": "user",
            "content": f"Extract the job details from this posting:\n\n{job_posting_text}",
        }
    ],
    temperature=0,
    max_tokens=1500,
    extra_body=NO_THINKING,
)

print(result.model_dump_json(indent=2))
