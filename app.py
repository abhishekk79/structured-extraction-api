import time
from collections import defaultdict

import gradio as gr
import instructor
from openai import OpenAI

from client import NO_THINKING, NVIDIA_MODEL, Settings
from main import SYSTEM_PROMPT
from main import client as embedded_client
from models import JobPosting

MAX_TEXT_LENGTH = 20000
RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SECONDS = 600

# In-memory only: resets on restart and isn't shared across worker processes.
# Fine for a single-instance demo Space, not a substitute for real rate limiting.
_call_log: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str, now: float | None = None) -> bool:
    """Return True and record a call if `ip` is under the free-tier limit."""
    now = time.time() if now is None else now
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    _call_log[ip] = [t for t in _call_log[ip] if t > window_start]
    if len(_call_log[ip]) >= RATE_LIMIT_MAX_CALLS:
        return False
    _call_log[ip].append(now)
    return True


def build_client(user_api_key: str):
    settings = Settings()
    raw_client = OpenAI(base_url=settings.nvidia_base_url, api_key=user_api_key)
    return instructor.from_openai(raw_client)


def extract_posting(text: str, user_api_key: str | None, ip: str) -> dict:
    if not text or not text.strip():
        return {"error": "Please paste a job posting."}
    if len(text) > MAX_TEXT_LENGTH:
        return {"error": f"Text is too long (max {MAX_TEXT_LENGTH:,} characters)."}

    if user_api_key:
        client = build_client(user_api_key)
    else:
        if not check_rate_limit(ip):
            minutes = RATE_LIMIT_WINDOW_SECONDS // 60
            return {
                "error": (
                    f"Demo limit reached ({RATE_LIMIT_MAX_CALLS} free requests per "
                    f"{minutes} min). Enter your own NVIDIA API key above to keep "
                    "testing, or try again later."
                )
            }
        client = embedded_client

    try:
        result = client.chat.completions.create(
            model=NVIDIA_MODEL,
            response_model=JobPosting,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Extract the job details from this posting:\n\n{text}",
                },
            ],
            temperature=0,
            max_tokens=1500,
            extra_body=NO_THINKING,
        )
        return result.model_dump()
    except Exception as exc:
        return {"error": f"Extraction failed: {exc}"}


def handle_submit(text: str, user_api_key: str | None, request: gr.Request | None) -> dict:
    ip = request.client.host if request and request.client else "unknown"
    return extract_posting(text, (user_api_key or "").strip() or None, ip)


with gr.Blocks(title="Structured Extraction API") as demo:
    gr.Markdown(
        "# Structured Extraction API\n"
        "Paste a job posting and get back structured JSON "
        "(title, seniority, skills, location, salary)."
    )
    text_input = gr.Textbox(
        label="Job posting",
        lines=10,
        placeholder="Paste a job posting here...",
    )
    with gr.Accordion("Advanced: use your own NVIDIA API key", open=False):
        gr.Markdown(
            f"The demo above shares a free tier of {RATE_LIMIT_MAX_CALLS} requests "
            f"per {RATE_LIMIT_WINDOW_SECONDS // 60} minutes per visitor. Paste your "
            "own NVIDIA API key here to bypass that limit and run extractions on "
            "your own account instead."
        )
        api_key_input = gr.Textbox(label="NVIDIA API key (optional)", type="password")
    submit_btn = gr.Button("Extract", variant="primary")
    output = gr.JSON(label="Extracted data")

    submit_btn.click(fn=handle_submit, inputs=[text_input, api_key_input], outputs=output)

if __name__ == "__main__":
    demo.launch()
