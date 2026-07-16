"""Builds a LangChain Embeddings object from decrypted LLM credentials, for
providers that support an embeddings API. Used only for live, in-memory
semantic matching (nothing produced here is ever persisted)."""
from __future__ import annotations

from typing import Any


def get_embeddings_from_credentials(creds: dict) -> Any | None:
    """Return an Embeddings instance for supported providers, or None if the
    provider has no embeddings API (e.g. anthropic, azure_openai) or the
    client could not be constructed (e.g. missing optional dependency)."""
    provider = creds.get("provider")
    try:
        if provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model="text-embedding-3-small", api_key=creds["api_key"])

        if provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=creds["api_key"])

        if provider == "bedrock":
            from langchain_aws import BedrockEmbeddings

            return BedrockEmbeddings(
                region_name=creds.get("region"),
                aws_access_key_id=creds["api_key"],
                aws_secret_access_key=creds["secret_key"],
            )
    except Exception:  # noqa: BLE001
        return None

    return None  # anthropic / azure_openai: no embeddings API supported here
