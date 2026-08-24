# Project Log: Structured Extraction API

Machine-readable summary of everything built in this project, for a
different AI agent picking up context cold. Written as a factual log, not
a pitch — includes bugs found, wrong turns, and open gaps, not just wins.

Repo: https://github.com/abhishekk79/structured-extraction-api (private)
Owner/builder: complete beginner (no prior coding background), built with
AI pair-programming across ~7 planned sessions plus a resume-polish pass.
Last verified commit: `fa750e2` on `main`, working tree clean, CI green.

## 1. What the project is

A small API that takes free-text job postings and extracts structured JSON
(title, seniority, skills, location, remote status, salary) validated
against a Pydantic schema, using an LLM via NVIDIA's OpenAI-compatible
endpoint (`integrate.api.nvidia.com`).

## 2. Tech stack (current, verified from source)

- Python 3.11.9, pyenv-virtualenv env `extraction-api`
- `openai` 1.109.1 — HTTP client for NVIDIA's OpenAI-compatible API
- `instructor` 1.3.2 — coerces LLM output into a validated Pydantic model
  via tool/function calling, with automatic retry on validation failure
- `pydantic` 2.13.4 — schema (`models.py`)
- `pydantic-settings` 2.15.0 — typed env-var config (`client.py`)
- `fastapi` 0.141.1 + `uvicorn[standard]` 0.52.4 — the `/extract` API
- `pytest` 9.1.1, `ruff` 0.16.4 — test suite and linting (dev-only, in
  `requirements-dev.txt`)
- NVIDIA model in use: `nvidia/nemotron-3-ultra-550b-a55b` (see §5 for why)

## 3. File inventory (what each file is for)

| Path | Purpose |
|---|---|
| `client.py` | Shared NVIDIA/OpenAI client. `Settings` (pydantic-settings) validates `NVIDIA_API_KEY`/`NVIDIA_BASE_URL`/`NVIDIA_MODEL` from `.env`. Exports `NO_THINKING` extra_body constant and `get_raw_client()`. |
| `models.py` | `JobPosting` Pydantic schema — the extraction target. |
| `main.py` | FastAPI app, single endpoint `POST /extract`. Input validated (`text` min_length=1); upstream LLM failures caught and returned as `502` (logged server-side via `logger.exception`, not leaked to the client). |
| `test_connection.py` | Manual script: sanity-checks API connectivity. Not part of the pytest suite (would call the real API). |
| `session1_raw_call.py` | Manual script: unstructured (plain-text) extraction, no schema. |
| `session2_structured_extraction.py` | Manual script: structured extraction via `instructor`, no HTTP layer. |
| `session4_stress_test.py` | Runs every file in `test_postings/` through the extraction logic concurrently (3 workers), writes results to `session4_results.json`. Catches per-posting failures instead of crashing the batch. |
| `test_postings/01-20*.txt` | 20 synthetic-but-realistic job postings, each targeting a specific edge case (see §6). Synthetic by design — avoids scraping/copyright issues and lets edge cases be deliberately engineered. |
| `sample_job_posting.txt` | Original Session 1-2 sample posting. |
| `tests/test_models.py` | Unit tests for `JobPosting` validation (no mocking needed). |
| `tests/test_client.py` | Tests `get_raw_client()` env wiring and `NO_THINKING` shape. |
| `tests/test_main.py` | FastAPI `TestClient` tests for `/extract`: success (LLM call mocked), missing/empty `text` → 422, upstream exception → 502. |
| `conftest.py` | Sets fake `NVIDIA_*` env vars **before** any project module is imported, so the whole suite runs offline with zero real API calls or secrets. |
| `pytest.ini` | Scopes pytest collection to `tests/` only — without this, pytest also collects `test_connection.py` (name matches `test_*.py`) and executes it at import time, which hits the real API and crashes collection. This actually happened once during development; fixed. |
| `pyproject.toml` | Ruff config: `line-length=100`, `target-version=py311`, rules `E,F,I,UP,B`. |
| `.github/workflows/ci.yml` | GitHub Actions: on push/PR to `main`, installs `requirements-dev.txt`, runs `ruff check .` then `pytest -v`. No secrets required (see conftest.py above). |
| `requirements.txt` / `requirements-dev.txt` | Runtime deps / dev-only deps (`-r requirements.txt` + pytest/httpx2/ruff). Split deliberately so a deployment install doesn't pull test tooling. |
| `LICENSE` | MIT. |
| `README.md` | User-facing docs: setup, running tests, curl example, roadmap. |
| `.env` (gitignored, not in repo) | `NVIDIA_API_KEY`, `NVIDIA_BASE_URL`, `NVIDIA_MODEL`. |

## 4. Chronological build log

**Session 0** — pyenv-virtualenv env created, deps installed, `.env` set up,
`test_connection.py` confirmed API connectivity.

**Session 1** — `session1_raw_call.py`: asked the model to extract fields as
plain text (no schema), to see raw model behavior before adding structure.

**Session 2** — `models.py` (`JobPosting`) + `session2_structured_extraction.py`
using `instructor.from_openai()` with `response_model=JobPosting`. Worked
first try, valid schema-matching JSON returned.

**Code review + GitHub setup** — reviewed Sessions 0-2 code before pushing
publicly. Found and fixed: `max_tokens=500` risked truncating longer
extractions (raised to 1500); `sample_job_posting.txt` opened via bare
relative path (broke outside project-root cwd, fixed via `Path(__file__)`);
client-setup boilerplate duplicated in 3 files (extracted to `client.py`);
no `requirements.txt` or `README.md` (added both, requirements pinned to
exact installed versions). Repo created as private, pushed to GitHub.

**Session 3** — `main.py`: wrapped Session 2's logic in `POST /extract`.
Verified live: started uvicorn, hit `/docs` (200), hit `/extract` with the
sample posting, got back correct structured JSON. Shipped via a feature
branch + PR (`session-3-fastapi-endpoint` → PR #1 → merged), the one time
in this project a PR workflow was used instead of direct-to-main commits.

**Session 4 — stress test round 1** — Built 10 synthetic job postings
targeting known-hard cases (hourly pay, no salary listed, EUR salary,
internship, terse/verbose text, India/INR, fully-remote/no-location,
ambiguous "mostly remote", non-tech role). Ran via a concurrent
(`ThreadPoolExecutor`, 3 workers) harness. **Found 2 real bugs:**
1. Hourly rates read as if they were the whole salary (e.g. "$45-60/hour"
   → `salary_max: 60`) — schema had no pay-period concept.
2. Non-USD salaries indistinguishable from USD (EUR 95k-120k and INR
   12-16 lakh both came back as bare integers) — schema had no currency
   field.

**Fix**: added `salary_period: Literal["hourly","annual"]` and
`currency: str` (ISO 4217) to `JobPosting`. Re-ran, confirmed both fixed.

**Model latency investigation** (mid-session, significant detour) —
Original model `deepseek-ai/deepseek-v4-flash-0731` took **4-6+ minutes
per call even for a one-line posting**. Tried disabling the model's
"thinking"/reasoning mode via `extra_body={"chat_template_kwargs":
{"thinking": False, "enable_thinking": False}}` (undocumented parameter,
confirmed via web research against community reports, not official NVIDIA
docs — no official reference confirms the exact key). **Result: no
latency improvement** (272s for a trivial call, same as before). Root
cause was the model itself, not thinking mode. User provided a different
model (`nvidia/nemotron-3-ultra-550b-a55b`) via a code snippet **that
included a live API key pasted in chat** — that pasted key was NOT
stored anywhere (not written to `.env`, not committed); the project kept
using its existing `.env` key, which turned out to still work against the
new model. Switching model dropped latency to **2-10 seconds per call**
(a ~30-100x improvement). The `NO_THINKING` extra_body was kept in the
code regardless (harmless, and matches NIM's documented pattern for
avoiding hangs on reasoning models) even though it wasn't the fix.

**Sessions 5-6 — expanded stress test** — Added 10 more postings (total
20): weekly pay, multiple listed locations, unpaid/volunteer role, base
salary + commission/OTE, executive-level role, GBP-symbol-only currency
(no "GBP" word), project-based flat fee, emoji/marketing-heavy title,
non-English (Spanish) posting, deliberately non-job-posting garbage text.
All 20 succeeded (no crashes). **Found 2 more real bugs:**
3. `salary_period` enum too narrow — weekly pay ($2,000/week) got forced
   into `"hourly"`; project-based flat fee ($6,000 for a project) got
   forced into `"annual"`. Both misleading.
4. Bonus/commission conflated into `salary_max` — a $110k base + $110k
   commission ($220k OTE) posting came back as `salary_min: 110000,
   salary_max: 220000`, reading like a normal $110k-220k base range when
   it's actually base-plus-variable mixed together.

**Fix**: expanded `salary_period` to `["hourly","weekly","project","annual"]`;
tightened `salary_min`/`salary_max` Field descriptions to explicitly
exclude bonus/commission/OTE. Re-ran, confirmed: weekly posting now
`period: weekly`, project posting now `period: project`, bonus posting's
`salary_max` dropped from 220000 to the correct 110000 (base only).

Notable non-bugs observed during this round (documented, not "fixed"):
multi-location postings joined cleanly into one location string; the
Spanish posting was extracted correctly (currency inferred from `€` and
European `55.000 €`-style number formatting parsed correctly) but the
**title was left in Spanish** rather than translated, while a separate
emoji/marketing-heavy title *was* normalized to a clean English title —
inconsistent behavior, no schema rule governs output language, left as a
known/undecided point rather than "fixed" one way or the other; garbage
non-job-posting input degraded gracefully to `"Unknown"`/`null` fields
instead of hallucinating a fake posting, despite `title`/`seniority`/
`location` being required (non-optional) string fields.

**Resume-polish round 1 — pytest suite** — Added `tests/` (13 tests
initially, later 14) covering `models.py`, `client.py`, `main.py`. Built
`conftest.py` to fake credentials before import so the suite is fully
offline. **Bug found and fixed during this step**: pytest's default
`test_*.py` collection pattern matched `test_connection.py` at the
project root (a manual connectivity script, not a real test) and tried
to execute it during collection, which made a real (failing, since fake
creds were in place) API call and crashed the whole test run. Fixed via
`pytest.ini` scoping collection to `tests/` only.

**Resume-polish round 2 — CI** — `.github/workflows/ci.yml`: runs on
push/PR to `main`, `pip install -r requirements-dev.txt` then `pytest
-v`. No secrets needed. Added a CI badge to the README. Verified the
workflow actually passes on GitHub (not just assumed from local passing
tests) via `gh run watch`. Bumped `actions/checkout`/`actions/setup-python`
from v4/v5 to v7 to clear a Node-20-deprecation annotation GitHub Actions
surfaced on the first real run.

**Resume-polish round 3 — polish pass** —
- `LICENSE` (MIT) added.
- `client.py` config rewritten to use `pydantic-settings` instead of raw
  `os.environ[...]` — a missing/invalid env var now produces one
  `ValidationError` listing every problem, instead of a bare `KeyError`
  on whichever var happens to be read first. Verified both the happy
  path (real `.env` still loads, `test_connection.py` still works) and
  the failure path (confirmed the clean validation-error output with env
  vars unset). `python-dotenv` dropped as a direct dependency (it's a
  transitive dep of `pydantic-settings`, which handles `.env` loading
  natively via `env_file=`).
- `/extract` given real error handling: empty `text` rejected at 422
  (Pydantic `min_length=1`); upstream LLM/instructor exceptions caught
  and turned into a 502 with a safe client-facing message, full exception
  logged server-side. Verified live against a running server (not just
  the mocked unit tests) for both the empty-text and success cases.
- `ruff` added (`pyproject.toml` config, rules `E,F,I,UP,B`, line-length
  100), wired into CI as a lint step before tests. **10 real findings on
  first run**, all fixed (not suppressed/ignored): unsorted imports,
  `Optional[X]` → `X | None`, 4 overlong description strings (wrapped),
  and one `raise ... from None` needed on the re-raised `HTTPException`
  in the new error-handling code.
- README: added a curl usage example — verified live against a running
  server, then corrected the example's expected `location` field value
  from an assumed `"Remote"` to the actually-observed `"remote"` so the
  doc reflects real output, not a guess.

## 5. Key decisions and why

- **Model choice**: originally `deepseek-ai/deepseek-v4-flash-0731`
  (chosen in an earlier session for confirmed tool-calling benchmark
  performance), replaced by `nvidia/nemotron-3-ultra-550b-a55b` after the
  former showed 4-6+ minute latency per call that a documented-but-
  unverified "disable thinking mode" parameter did not fix. This was a
  user-directed switch, not independently re-litigated.
- **Synthetic test postings over scraped real ones**: avoids copyright/
  scraping concerns and allows edge cases to be deliberately engineered
  (a real job board wouldn't reliably surface "GBP symbol with no GBP
  word" or "salary in a Spanish posting" on demand).
- **Direct-to-main commits, mostly**: only Session 3 used a feature
  branch + PR (at explicit user request via a `/create-pr-command`
  invocation); every other session/fix was committed directly to `main`
  after local verification. Not a strict rule, just what happened.
- **Mocking the LLM in tests, not recording/replaying real responses**:
  keeps the suite deterministic, free, and fast (~1s for 14 tests) at
  the cost of not catching real-model regressions — those are still only
  caught by the manual `session4_stress_test.py` run against the live API.

## 6. Test coverage map (`test_postings/`, 20 files)

`01` hourly contract pay · `02` no salary published · `03` EUR salary ·
`04` internship/hourly · `05` terse one-liner · `06` long/verbose posting ·
`07` India/INR salary · `08` fully remote, no fixed location · `09`
ambiguous "mostly remote with travel" · `10` non-tech role · `11` weekly
pay · `12` multiple listed locations · `13` unpaid/volunteer · `14` base
salary + commission/OTE · `15` executive-level, prose-heavy (no bullet
skills list) · `16` GBP symbol only, no "GBP" text · `17` project-based
flat fee · `18` emoji/marketing-heavy title · `19` non-English (Spanish) ·
`20` deliberately non-job-posting garbage text.

`session4_results.json` holds the latest full run's output (20/20 success
as of the last run referenced in this log).

## 7. Current known gaps / explicitly NOT done

- **No live deployment** (Session 7 of the original plan: Hugging Face
  Spaces). This is the biggest gap for a resume link — README claims
  functionality but there's nothing an interviewer can hit directly yet.
- **Sync OpenAI client in an async framework** — `main.py`'s `/extract`
  is a sync `def` calling a blocking `OpenAI` client inside FastAPI.
  Works (FastAPI runs sync defs in a threadpool) but isn't using
  `AsyncOpenAI`/`async def`, which would be more idiomatic and scale
  better under concurrent load. Explicitly deferred, not forgotten.
- **No written "latency debugging story"** — the model-swap investigation
  in §4 is a strong, concrete engineering narrative (profiled, formed a
  hypothesis, tested it, hypothesis failed, found the real cause, fixed
  it, verified the fix) but currently lives only in git history/this log,
  not in a polished README/DESIGN.md section aimed at a reader.
  Deferred, not forgotten.
- **Title-language inconsistency** (§4, Sessions 5-6) — no rule decided
  on whether output fields should be normalized to English regardless of
  input language. Currently inconsistent (see the Spanish-vs-emoji-title
  example above). Not fixed either direction.
- **No rate limiting or auth on `/extract`** — fine for a local demo, a
  real concern if actually deployed publicly.
- **No CONTRIBUTING.md, no Docker support, no structured request
  logging/observability, no cost/latency tracking beyond the manual
  stress-test timings.**
- **Eval quality**: `session4_results.json` is a pass/fail-plus-timing
  log, not a scored accuracy report against hand-labeled "golden"
  expected values — correctness for the 20 postings was verified by
  manual inspection during Sessions 4-6, not by automated assertions.

## 8. Verification state as of this log

- `git status`: clean. `main` local == `origin/main` (commit `fa750e2`).
- `pytest`: 14/14 passing, ~0.7-1s runtime, zero network calls.
- `ruff check .`: clean, zero findings.
- CI (`gh run watch`, not just assumed): last run green — checkout,
  setup-python, install, lint, test all passed.
- Live server smoke test (this session): `/docs` → 200, empty `text` →
  422 with expected Pydantic error body, valid posting → 200 with
  correctly structured JSON, verified against the exact curl command
  documented in the README.

## 9. If you are the agent picking this up next

Start by reading `README.md` for the user-facing framing, then this file
for the full history. The most valuable next step per the last in-session
discussion was **Session 7 (deployment)** or, if continuing the resume-
polish thread, the **async client rewrite** or the **latency-story
writeup** (§7). Don't re-litigate the model choice, the direct-to-main
commit pattern, or synthetic-vs-real test data — those were deliberate,
discussed decisions, not defaults that slipped through.
