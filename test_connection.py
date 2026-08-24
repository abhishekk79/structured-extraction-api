from client import NVIDIA_MODEL, get_raw_client

client = get_raw_client()

completion = client.chat.completions.create(
    model=NVIDIA_MODEL,
    messages=[{"role": "user", "content": "Reply with exactly: connection ok"}],
    temperature=0,
    max_tokens=20,
)

print(completion.choices[0].message.content)
