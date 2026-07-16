"""Instantiate + cache LangChain chat model objects from decrypted LLMConfig
credentials. Mirrors ai-service/services/llm_factory.py's provider-normalisation
and caching pattern, extended to the 5 supported providers.
"""
from __future__ import annotations

import hashlib
from typing import Any

_llm_cache: dict[str, Any] = {}


def _cache_key(creds: dict) -> str:
    fingerprint = "|".join(
        str(creds.get(k)) for k in ("provider", "model_name", "api_key", "secret_key", "base_url", "region", "api_version")
    )
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def get_llm_from_credentials(creds: dict, temperature: float = 0.0):
    """Build (or reuse a cached) LangChain chat model instance for the given credentials."""
    key = _cache_key(creds)
    if key in _llm_cache:
        return _llm_cache[key]

    provider = creds["provider"]
    model_name = creds["model_name"]

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model_name, api_key=creds["api_key"], temperature=temperature)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        # langchain_anthropic defaults max_tokens to just 1024, which silently
        # truncates replies (e.g. a markdown table for a few dozen rows) mid-
        # generation with stop_reason="max_tokens". Raise the cap so normal-sized
        # chat replies (including full result tables) aren't cut off.
        llm = ChatAnthropic(model=model_name, api_key=creds["api_key"], temperature=temperature, max_tokens=8192)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=creds["api_key"], temperature=temperature)

    elif provider == "azure_openai":
        from langchain_openai import AzureChatOpenAI

        llm = AzureChatOpenAI(
            azure_endpoint=creds["base_url"],
            api_key=creds["api_key"],
            api_version=creds.get("api_version") or "2024-06-01",
            azure_deployment=model_name,
            temperature=temperature,
        )

    elif provider == "bedrock":
        from langchain_aws import ChatBedrockConverse

        llm = ChatBedrockConverse(
            model=model_name,
            region_name=creds.get("region"),
            aws_access_key_id=creds["api_key"],
            aws_secret_access_key=creds["secret_key"],
            temperature=temperature,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    _llm_cache[key] = llm
    return llm


def clear_cache() -> None:
    _llm_cache.clear()


def extract_provider_error_message(exc: Exception) -> str:
    """Best-effort extraction of a clean, human-readable message from a provider
    SDK exception.

    str(exc) for some SDKs (e.g. OpenAI/Anthropic's APIStatusError) embeds a raw
    Python-dict-repr of the whole HTTP error body (e.g. "Error code: 401 -
    {'error': {'message': '...'}}"), which looks like broken JSON to end users.
    This digs into the SDK's structured attributes to pull out just the message.
    """
    # OpenAI / Anthropic style: exc.body is a parsed dict like {"error": {"message": "..."}}
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(body.get("message"), str):
            return body["message"]

    # boto3 ClientError style: exc.response["Error"]["Message"]
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        error = response.get("Error")
        if isinstance(error, dict) and isinstance(error.get("Message"), str):
            return error["Message"]

    # Generic SDKs that expose a clean `.message` attribute
    message = getattr(exc, "message", None)
    if isinstance(message, str) and message.strip():
        return message

    return str(exc)


def validate_llm_credentials(creds: dict) -> None:
    """Make a minimal real call to the provider to confirm the given credentials
    (api key/secret, model name, endpoint, region, etc.) actually work.

    Raises ValueError with a human-readable message if the provider rejects the
    credentials/model or the call otherwise fails.
    """
    try:
        llm = get_llm_from_credentials(creds, temperature=0.0)
        llm.invoke("ping")
    except Exception as exc:  # noqa: BLE001 - surface the provider's own error to the caller
        raise ValueError(f"Could not validate LLM credentials: {extract_provider_error_message(exc)}") from exc
