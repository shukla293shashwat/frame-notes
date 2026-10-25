"""Select the configured chat model provider."""

import os


def selected_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()


def required_api_key_name() -> str | None:
    provider = selected_provider()
    if provider == "ollama":
        return "OLLAMA_API_KEY" if os.getenv("OLLAMA_MODE", "local").strip().lower() == "cloud" else None
    if provider == "groq":
        return "GROQ_API_KEY"
    if provider == "mistral":
        return "MISTRAL_API_KEY"
    raise ValueError("Unsupported LLM_PROVIDER. Choose 'ollama', 'mistral', or 'groq'.")


def get_llm(temperature: float = 0.3):
    provider = selected_provider()
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        mode = os.getenv("OLLAMA_MODE", "local").strip().lower()
        if mode == "cloud":
            return ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "gemma4:31b"),
                base_url="https://ollama.com",
                client_kwargs={"headers": {"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY', '')}"}},
                temperature=temperature,
            )
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
        )
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
            max_retries=3,
        )
    if provider == "mistral":
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=temperature,
            max_retries=3,
        )
    raise ValueError("Unsupported LLM_PROVIDER. Choose 'ollama', 'mistral', or 'groq'.")
