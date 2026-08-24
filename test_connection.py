import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["NVIDIA_BASE_URL"],
    api_key=os.environ["NVIDIA_API_KEY"],
)

completion = client.chat.completions.create(
    model=os.environ["NVIDIA_MODEL"],
    messages=[{"role": "user", "content": "Reply with exactly: connection ok"}],
    temperature=0,
    max_tokens=20,
)

print(completion.choices[0].message.content)
