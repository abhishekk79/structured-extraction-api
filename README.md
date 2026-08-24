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
   NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
   ```

   `deepseek-ai/deepseek-v4-flash-0731` was used originally but showed
   multi-minute latency per call regardless of settings; `nemotron-3-ultra`
   responds in a few seconds for the same extraction task.

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
| `main.py` | FastAPI app exposing `POST /extract` (Session 3). |
| `test_postings/` | Varied job postings (hourly pay, foreign currency, no salary, terse/verbose, etc.) used to stress-test extraction (Session 4). |
| `session4_stress_test.py` | Runs every file in `test_postings/` through the extraction logic and writes results to `session4_results.json` (Session 4). |
| `tests/` | Automated pytest suite for `models.py`, `client.py`, and `main.py`. Mocks every LLM call — no API key or network access needed. |

## Running the tests

Install dev dependencies (adds `pytest` and test-only extras on top of
`requirements.txt`), then run:

```bash
pip install -r requirements-dev.txt
pytest
```

The suite never calls the real NVIDIA API — `conftest.py` sets fake
credentials before any project module is imported, and the FastAPI endpoint
tests mock the LLM call directly, so it runs in about a second with no
API key required. `test_connection.py` and `session1-4` scripts are separate,
manual scripts (they hit the real API) and aren't part of the pytest suite.

## Running the scripts

Each script can be run directly; they all read `sample_job_posting.txt` from
the project root regardless of your current working directory:

```bash
python session1_raw_call.py
python session2_structured_extraction.py
```

To run the API server and stress test:

```bash
uvicorn main:app --reload
python session4_stress_test.py
```

## Roadmap

- [x] Session 0: environment setup + API connectivity test
- [x] Session 1: raw (unstructured) field extraction
- [x] Session 2: structured extraction with Pydantic + instructor
- [x] Session 3: wrap extraction in a FastAPI `POST /extract` endpoint
- [x] Session 4: stress-test against varied postings, fix salary period/currency ambiguity
- [x] Session 5-6: expand test coverage to 20 postings (multi-location, unpaid roles, bonus/OTE, non-English, garbage input), fix weekly/project pay periods
- [ ] Session 7: deploy to Hugging Face Spaces
