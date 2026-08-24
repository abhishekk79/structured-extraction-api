from pathlib import Path

from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    nvidia_api_key: str
    nvidia_base_url: str
    nvidia_model: str


NVIDIA_MODEL = Settings().nvidia_model

# Disables the model's extended reasoning/"thinking" mode. NVIDIA NIM's exact
# parameter name for this isn't consistently documented across their reasoning
# models, so both known variants are set.
NO_THINKING = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}


def get_raw_client() -> OpenAI:
    """OpenAI-compatible client pointed at the NVIDIA integrate endpoint."""
    settings = Settings()
    return OpenAI(base_url=settings.nvidia_base_url, api_key=settings.nvidia_api_key)
