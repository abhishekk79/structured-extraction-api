import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["NVIDIA_BASE_URL"],
    api_key=os.environ["NVIDIA_API_KEY"],
)

with open("sample_job_posting.txt") as f:
    job_posting = f.read()

prompt = f"""Extract the following fields from this job posting as plain text
(no JSON yet, just describe what you find):
- job title
- seniority level
- required skills
- location
- is it remote?
- salary range

Job posting:
{job_posting}
"""

completion = client.chat.completions.create(
    model=os.environ["NVIDIA_MODEL"],
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    max_tokens=500,
)

print(completion.choices[0].message.content)
