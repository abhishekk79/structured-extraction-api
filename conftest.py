import os

# Set fake NVIDIA credentials before any project module is imported, so the
# test suite never depends on (or accidentally uses) a real .env / API key.
# setdefault means a real .env is still respected if a var is already set in
# the environment, but nothing here ever calls the live API.
os.environ.setdefault("NVIDIA_API_KEY", "test-api-key")
os.environ.setdefault("NVIDIA_BASE_URL", "https://example.invalid/v1")
os.environ.setdefault("NVIDIA_MODEL", "test-model")
