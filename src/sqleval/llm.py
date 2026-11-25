"""Minimal client for Groq's OpenAI-compatible chat API."""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def ask(model, messages, retries=5, timeout=60):
    """Send messages to the model. Returns (reply_text, usage_dict, seconds_taken)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,   # as repeatable as possible, so runs can be compared fairly
        "max_tokens": 4000,  # room for the model's hidden reasoning plus the answer
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(1, retries + 1):
        start = time.perf_counter()
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            print(f"  network error ({exc}); retry {attempt}/{retries}")
            time.sleep(5 * attempt)
            continue
        seconds = time.perf_counter() - start

        if response.status_code == 429 or response.status_code >= 500:
            wait = float(response.headers.get("retry-after", 5 * attempt))
            print(f"  HTTP {response.status_code}; waiting {wait:.0f}s (retry {attempt}/{retries})")
            time.sleep(wait)
            continue
        if response.status_code >= 400:  # other errors (bad key, unknown model) fail immediately
            raise RuntimeError(f"Groq error {response.status_code}: {response.text[:300]}")

        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply, data.get("usage", {}), seconds

    raise RuntimeError(f"Gave up after {retries} attempts")
