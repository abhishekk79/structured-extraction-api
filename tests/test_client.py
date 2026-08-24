from client import NO_THINKING, get_raw_client


def test_get_raw_client_uses_env_config(monkeypatch):
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake-key-123")

    client = get_raw_client()

    assert str(client.base_url) == "https://example.invalid/v1/"
    assert client.api_key == "fake-key-123"


def test_no_thinking_disables_both_known_parameter_names():
    kwargs = NO_THINKING["chat_template_kwargs"]
    assert kwargs["thinking"] is False
    assert kwargs["enable_thinking"] is False
