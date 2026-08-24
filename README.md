# Structured Extraction API

A small project that extracts structured data (job title, seniority, skills,
location, remote status, salary range) from free-text job postings using an
LLM, and validates the result against a [Pydantic](https://docs.pydantic.dev/)
schema via [instructor](https://python.useinstructor.com/).

The model is served by NVIDIA's OpenAI-compatible `integrate.api.nvidia.com`
endpoint.

## Setup

1. Create and activate a Python 3.11 virtual environment (this project was
   built with `pyenv-virtualenv`, but any `venv` works).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (this file is gitignored and
   never committed) with:

   ```bash
   NVIDIA_API_KEY=your-nvidia-api-key
   NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
   NVIDIA_MODEL=deepseek-ai/deepseek-v4-flash-0731
   ```

4. Verify the connection:

   ```bash
   python test_connection.py
   ```

   This should print `connection ok`.

## Project structure

| File | Purpose |
|---|---|
| `client.py` | Shared NVIDIA/OpenAI client setup, reused by every script. |
| `models.py` | The `JobPosting` Pydantic schema the model's output is validated against. |
| `sample_job_posting.txt` | A realistic sample job posting used as test input. |
| `test_connection.py` | Sanity-checks the API connection (Session 0). |
| `session1_raw_call.py` | Asks the model to extract fields as plain text, no schema (Session 1). |
| `session2_structured_extraction.py` | Uses `instructor` + `JobPosting` to get validated structured JSON (Session 2). |

## Running the scripts

Each script can be run directly; they all read `sample_job_posting.txt` from
the project root regardless of your current working directory:

```bash
python session1_raw_call.py
python session2_structured_extraction.py
```

Note: the model runs in a high-reasoning "thinking" mode and can take
1-3+ minutes to respond — this is expected.

## Roadmap

- [x] Session 0: environment setup + API connectivity test
- [x] Session 1: raw (unstructured) field extraction
- [x] Session 2: structured extraction with Pydantic + instructor
- [ ] Session 3: wrap extraction in a FastAPI `POST /extract` endpoint
- [ ] Session 4-6: stress-test against 20-25 real job postings, fix issues
- [ ] Session 7: deploy to Hugging Face Spaces
