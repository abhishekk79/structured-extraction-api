import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import instructor

from client import NO_THINKING, NVIDIA_MODEL, PROJECT_ROOT, get_raw_client
from models import JobPosting

POSTINGS_DIR = PROJECT_ROOT / "test_postings"
RESULTS_PATH = PROJECT_ROOT / "session4_results.json"
MAX_WORKERS = 3

client = instructor.from_openai(get_raw_client())


def extract_one(path: Path) -> dict:
    text = path.read_text()
    start = time.monotonic()
    try:
        result = client.chat.completions.create(
            model=NVIDIA_MODEL,
            response_model=JobPosting,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the job details from this posting:\n\n{text}",
                }
            ],
            temperature=0,
            max_tokens=1500,
            extra_body=NO_THINKING,
        )
        return {
            "file": path.name,
            "ok": True,
            "seconds": round(time.monotonic() - start, 1),
            "result": result.model_dump(),
        }
    except Exception as exc:
        return {
            "file": path.name,
            "ok": False,
            "seconds": round(time.monotonic() - start, 1),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    postings = sorted(POSTINGS_DIR.glob("*.txt"))
    print(f"Running {len(postings)} postings through /extract logic ({MAX_WORKERS} at a time)...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(extract_one, p): p for p in postings}
        for future in as_completed(futures):
            outcome = future.result()
            status = "OK" if outcome["ok"] else "FAIL"
            print(f"[{status}] {outcome['file']} ({outcome['seconds']}s)")
            results.append(outcome)

    results.sort(key=lambda r: r["file"])
    RESULTS_PATH.write_text(json.dumps(results, indent=2))

    ok_count = sum(1 for r in results if r["ok"])
    print(f"\n{ok_count}/{len(results)} succeeded. Full results written to {RESULTS_PATH.name}")


if __name__ == "__main__":
    main()
