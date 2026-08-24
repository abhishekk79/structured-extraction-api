import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
NVIDIA_MODEL = os.environ["NVIDIA_MODEL"]


def get_raw_client() -> OpenAI:
    """OpenAI-compatible client pointed at the NVIDIA integrate endpoint."""
    return OpenAI(
        base_url=os.environ["NVIDIA_BASE_URL"],
        api_key=os.environ["NVIDIA_API_KEY"],
    )
