"""Pluggable LLM access.

Both methods in this pipeline (the direct baseline and the graph pipeline's
node/edge extraction stages) call `complete(prompt, schema)` and nothing else,
so a concrete provider can be dropped in without touching pipeline code.
`GroqLLMClient` and `FeatherlessLLMClient` are real (non-fixture) providers,
both calling open models through an OpenAI-compatible chat completions API.
"""

import json
import os
import re
import time
from abc import ABC, abstractmethod

import requests


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt, schema):
        """Send `prompt`, constrained to return JSON matching `schema`, and return the parsed dict."""
        raise NotImplementedError


class FixtureLLMClient(LLMClient):
    """Testing/demo client: returns pre-recorded responses instead of calling a model.

    `responses` is a list of dicts, consumed in order (one per `complete()` call) so a
    pipeline run's fixed sequence of stage calls can be scripted for tests or a mock
    end-to-end demo without any live API key.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self._calls = []

    def complete(self, prompt, schema):
        self._calls.append({"prompt": prompt, "schema": schema})
        if not self._responses:
            raise RuntimeError("FixtureLLMClient ran out of scripted responses")
        return self._responses.pop(0)

    @property
    def calls(self):
        return list(self._calls)


class _OpenAICompatibleClient(LLMClient):
    """Shared implementation for providers exposing an OpenAI-style chat
    completions endpoint with JSON mode. Subclasses set `_url`, `_default_model`,
    and `_api_key_env`.

    JSON mode guarantees syntactically valid JSON but doesn't enforce the
    schema itself, so the target schema is spelled out in the system prompt
    and a response missing required keys (or truncated mid-generation on a
    long story) is retried, with the validation error fed back to the model,
    up to `max_retries` times.
    """

    _url = None
    _default_model = None
    _api_key_env = None

    def __init__(self, model=None, api_key=None, max_retries=7):
        self._model = model or self._default_model
        self._api_key = api_key or os.environ.get(self._api_key_env)
        if not self._api_key:
            raise RuntimeError(f"{self._api_key_env} is not set.")
        self._max_retries = max_retries
        self._calls = []

    def _post(self, payload):
        """POST with backoff on 429 (free/shared tiers are rate-limited)."""
        response = None
        for attempt in range(8):
            try:
                response = requests.post(
                    self._url,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                    timeout=240,
                )
            except requests.exceptions.RequestException as exc:
                print(f"    [{type(self).__name__}] network error ({exc}); retrying...", flush=True)
                time.sleep(5.0 * (attempt + 1))
                continue
            if response.status_code != 429:
                return response
            match = re.search(r"try again in ([\d.]+)s", response.text)
            wait = float(match.group(1)) + 0.5 if match else 5.0
            time.sleep(wait)
        if response is None:
            raise RuntimeError(f"{type(self).__name__}: repeated network errors, no response received")
        return response

    def complete(self, prompt, schema):
        system = (
            "You are a precise information-extraction assistant. Respond with a single "
            "JSON object and nothing else, matching this JSON schema exactly. Every key "
            "listed in the schema's top-level `required` array MUST be present in your "
            "output even if its value is an empty array or list -- never omit a required "
            "key just because you have nothing to report for it.\n" + json.dumps(schema)
        )
        user_prompt = prompt
        last_error = None

        for attempt in range(self._max_retries + 1):
            print(f"    [{type(self).__name__}] {self._model} attempt {attempt + 1}/{self._max_retries + 1}...", flush=True)
            t0 = time.time()
            response = self._post({
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
                "max_tokens": 8192,
            })
            print(f"    [{type(self).__name__}] -> HTTP {response.status_code} in {time.time() - t0:.1f}s", flush=True)
            if not response.ok:
                last_error = f"HTTP {response.status_code}: {response.text}"
                user_prompt = f"{prompt}\n\nYour previous reply was invalid ({last_error}). Return ONLY valid JSON matching the schema."
                time.sleep(1.5)
                continue
            try:
                content = response.json()["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                # The HTTP envelope itself was malformed/truncated (e.g. a
                # dropped connection after a gateway timeout) -- a transport
                # fault, not an invalid model reply, so just retry the same
                # request rather than telling the model its answer was bad.
                last_error = f"malformed response envelope: {exc}"
                print(f"    [{type(self).__name__}] {last_error}; retrying...", flush=True)
                time.sleep(2.0)
                continue
            self._calls.append({"prompt": prompt, "schema": schema, "raw_response": content})

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                last_error = f"invalid JSON: {exc}"
                user_prompt = f"{prompt}\n\nYour previous reply was invalid ({last_error}). Return ONLY valid JSON matching the schema."
                continue

            missing = [key for key in schema.get("required", []) if key not in parsed]
            if missing:
                last_error = f"missing required keys: {missing}"
                user_prompt = f"{prompt}\n\nYour previous reply was invalid ({last_error}). Return ONLY valid JSON matching the schema."
                continue

            return parsed

        raise RuntimeError(f"{type(self).__name__} failed after {self._max_retries + 1} attempts: {last_error}")

    @property
    def calls(self):
        return list(self._calls)


class GroqLLMClient(_OpenAICompatibleClient):
    """Calls a free-tier open model via Groq. Requires GROQ_API_KEY
    (free key at console.groq.com/keys). Free tier is rate-limited to a few
    thousand tokens/minute, so long stories can be slow."""

    _url = "https://api.groq.com/openai/v1/chat/completions"
    _default_model = "openai/gpt-oss-120b"
    _api_key_env = "GROQ_API_KEY"


class FeatherlessLLMClient(_OpenAICompatibleClient):
    """Calls an open model via Featherless's OpenAI-compatible API. Requires
    FEATHERLESS_API_KEY (a paid Featherless subscription)."""

    _url = "https://api.featherless.ai/v1/chat/completions"
    _default_model = "meta-llama/Llama-3.3-70B-Instruct"
    _api_key_env = "FEATHERLESS_API_KEY"
