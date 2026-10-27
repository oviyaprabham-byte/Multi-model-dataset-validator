"""
llm_service.py  — Provider-agnostic LLM integration.

Configuration via environment variables:
    LLM_PROVIDER = none | openai | anthropic | google | ollama
    LLM_API_KEY  = <your key>
    LLM_MODEL    = <model name>

If LLM_PROVIDER is "none" or not set, the service returns a clear
"LLM is not configured" message — it never pretends to generate a response.

All providers are imported lazily so missing optional packages don't crash
the server at startup.
"""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars work without it


def _get_config():
    provider = os.getenv("LLM_PROVIDER", "none").lower().strip()
    api_key  = os.getenv("LLM_API_KEY", "").strip()
    model    = os.getenv("LLM_MODEL", "").strip()
    return provider, api_key, model


def is_llm_configured() -> bool:
    provider, api_key, _ = _get_config()
    return provider not in ("none", "", "null") and bool(api_key or provider == "ollama")


def get_llm_status() -> dict:
    provider, api_key, model = _get_config()
    configured = is_llm_configured()
    return {
        "configured": configured,
        "provider":   provider if configured else None,
        "model":      model    if configured else None,
    }


def get_llm_answer(context: str, question: str) -> str:
    """
    Ask an LLM a question given a context string.

    Returns:
        The LLM's answer, or a descriptive message if LLM is not configured.
    """
    provider, api_key, model = _get_config()

    if provider in ("none", "", "null") or (not api_key and provider != "ollama"):
        return _NOT_CONFIGURED_MSG

    try:
        if provider == "openai":
            return _ask_openai(context, question, api_key, model or "gpt-4o-mini")
        elif provider == "anthropic":
            return _ask_anthropic(context, question, api_key, model or "claude-3-haiku-20240307")
        elif provider == "google":
            return _ask_google(context, question, api_key, model or "gemini-1.5-flash")
        elif provider == "ollama":
            return _ask_ollama(context, question, model or "llama3")
        else:
            return f"LLM provider '{provider}' is not supported. Supported: openai, anthropic, google, ollama, none."
    except Exception as e:
        return f"LLM error: {str(e)}"


# ── Provider implementations ──────────────────────────────────────────────────

_SYS_PROMPT = (
    "You are a dataset analysis assistant. Answer the user's question using ONLY "
    "the dataset documentation provided below. Be concise and natural. "
    "If the information is not in the documentation, say: "
    "'This information is not available in the documentation.'"
    "\n\nDo NOT invent or guess information."
)

_NOT_CONFIGURED_MSG = (
    "LLM is not configured. To enable AI-powered answers, set LLM_PROVIDER, "
    "LLM_API_KEY, and LLM_MODEL in the backend .env file. "
    "Basic document reading via voice is still available."
)


def _ask_openai(context: str, question: str, api_key: str, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return "OpenAI package not installed. Run: pip install openai"

    client = OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": _SYS_PROMPT},
        {"role": "user",   "content": f"DOCUMENTATION:\n{context}\n\nQUESTION: {question}"},
    ]
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=512)
    return response.choices[0].message.content.strip()


def _ask_anthropic(context: str, question: str, api_key: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        return "Anthropic package not installed. Run: pip install anthropic"

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=512,
        system=_SYS_PROMPT,
        messages=[
            {"role": "user", "content": f"DOCUMENTATION:\n{context}\n\nQUESTION: {question}"}
        ],
    )
    return msg.content[0].text.strip()


def _ask_google(context: str, question: str, api_key: str, model: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        return "Google Generative AI package not installed. Run: pip install google-generativeai"

    genai.configure(api_key=api_key)
    gmodel = genai.GenerativeModel(model)
    prompt = (
        f"{_SYS_PROMPT}\n\nDOCUMENTATION:\n{context}\n\nQUESTION: {question}"
    )
    response = gmodel.generate_content(prompt)
    return response.text.strip()


def _ask_ollama(context: str, question: str, model: str) -> str:
    try:
        import requests
    except ImportError:
        return "requests package not installed."

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYS_PROMPT},
            {"role": "user",   "content": f"DOCUMENTATION:\n{context}\n\nQUESTION: {question}"},
        ],
        "stream": False,
    }
    resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()
