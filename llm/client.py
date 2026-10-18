"""Universal LLM Client for Free & Commercial LLM Providers.

Uses python's standard `requests` library (synchronous & streaming) with support for:
- Standard OpenAI-compatible endpoints (Groq, Mistral, OpenRouter, Together, etc.)
- Google Gemini (via OpenAI compatibility endpoint and direct v1beta REST)
- Cohere v2 Chat API
- Hugging Face Inference API
- Keyless/Anonymous inference providers (OVHcloud, LLM7.io)
"""

import os
import time
import json
import requests
from typing import Dict, List, Any, Optional, Callable
from .provider_catalog import catalog, PROVIDER_ENV_KEYS, PROVIDER_TYPES

DEFAULT_TIMEOUT = 65.0


class LLMClient:
    """Dispatches chat completions to any provider in the catalog."""

    def __init__(self):
        self.catalog = catalog

    def get_api_key(self, provider_name: str, custom_key: Optional[str] = None) -> Optional[str]:
        """Resolves API key from parameter or environment variable."""
        if custom_key and custom_key.strip():
            return custom_key.strip()

        env_var = PROVIDER_ENV_KEYS.get(provider_name, f"{provider_name.upper().replace(' ', '_')}_KEY")
        key = os.getenv(env_var)
        if key:
            return key.strip()

        # Check common aliases
        lower = provider_name.lower()
        if "groq" in lower:
            return os.getenv("GROQ_API_KEY")
        elif "gemini" in lower or "google" in lower:
            return os.getenv("GEMINI_API_KEY")
        elif "openrouter" in lower:
            return os.getenv("OPENROUTER_API_KEY")
        elif "mistral" in lower:
            return os.getenv("MISTRAL_API_KEY")
        elif "hugging" in lower:
            return os.getenv("HF_API_KEY")
        elif "cohere" in lower:
            return os.getenv("COHERE_API_KEY")

        return None

    def resolve_endpoint_and_headers(
        self, provider_name: str, base_url: str, model_id: str, api_key: Optional[str] = None
    ) -> tuple[str, dict, dict]:
        """Resolves full URL, headers, and any body payload overrides."""
        p_info = self.catalog.get(provider_name)
        p_type = p_info.get("endpointType", "standard") if p_info else "standard"
        clean_base = base_url.rstrip("/")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AgySeo-BlogArchitect/3.8 (Windows NT; InersiaLab)",
        }

        # Google Gemini
        if p_type == "gemini" or "generativelanguage.googleapis.com" in clean_base:
            # Gemini supports OpenAI-compatible /v1beta/openai/chat/completions with Bearer token
            if clean_base.endswith("/v1beta"):
                url = f"{clean_base}/openai/chat/completions"
            elif "/v1beta/" in clean_base:
                url = f"{clean_base}/chat/completions"
            else:
                url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # Cohere
        if p_type == "cohere" or "api.cohere.com" in clean_base:
            url = f"{clean_base}/v2/chat" if not clean_base.endswith("/v2/chat") else clean_base
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # OpenRouter
        if "openrouter" in provider_name.lower():
            url = f"{clean_base}/chat/completions" if not clean_base.endswith("/chat/completions") else clean_base
            headers["HTTP-Referer"] = "http://127.0.0.1:8765"
            headers["X-Title"] = "InersiaLab SEO Blog Architect"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # Groq
        if "groq" in provider_name.lower():
            url = "https://api.groq.com/openai/v1/chat/completions"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # Mistral
        if "mistral" in provider_name.lower():
            url = "https://api.mistral.ai/v1/chat/completions"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # Cloudflare Workers AI
        if p_type == "cloudflare":
            account_id = os.getenv("CF_ACCOUNT_ID", "")
            resolved = clean_base.replace("{account_id}", account_id)
            url = f"{resolved}/{model_id}"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, {}

        # Standard OpenAI-Compatible Fallback
        if clean_base.endswith("/chat/completions"):
            url = clean_base
        elif clean_base.endswith("/v1"):
            url = f"{clean_base}/chat/completions"
        else:
            url = f"{clean_base}/chat/completions"

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        return url, headers, {}

    def test_connection(
        self, provider_name: str, model_id: str, custom_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pings provider with a minimal test message to verify key validity and measure latency."""
        p_info = self.catalog.get(provider_name)
        if not p_info:
            return {"success": False, "error": f"Unknown provider '{provider_name}'."}

        key = self.get_api_key(provider_name, custom_key)
        is_keyless = p_info.get("isKeyless", False)

        if not key and not is_keyless:
            return {
                "success": False,
                "error": f"API key required for {provider_name}. Please provide a key in the settings.",
            }

        base_url = p_info.get("baseUrl") or "https://api.openai.com/v1"
        url, headers, _ = self.resolve_endpoint_and_headers(provider_name, base_url, model_id, key)

        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Respond with the single word: OK"}
            ],
            "max_tokens": 10,
            "temperature": 0.1,
            "stream": False
        }

        start_time = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15.0)
            elapsed_ms = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                data = resp.json()
                content = ""
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                elif "message" in data:
                    content = data["message"].get("content", "")
                return {
                    "success": True,
                    "status": 200,
                    "latency_ms": elapsed_ms,
                    "provider": provider_name,
                    "model": model_id,
                    "reply": (content or "OK").strip(),
                }
            else:
                err_text = resp.text[:300]
                return {
                    "success": False,
                    "status": resp.status_code,
                    "latency_ms": elapsed_ms,
                    "provider": provider_name,
                    "model": model_id,
                    "error": f"HTTP {resp.status_code}: {err_text}",
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "latency_ms": int((time.time() - start_time) * 1000),
                "provider": provider_name,
                "model": model_id,
                "error": "Connection timed out after 15 seconds.",
            }
        except Exception as e:
            return {
                "success": False,
                "latency_ms": int((time.time() - start_time) * 1000),
                "provider": provider_name,
                "model": model_id,
                "error": str(e),
            }

    def generate(
        self,
        provider_name: str,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        custom_key: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Calls the LLM with messages and returns {content, latency_ms, stats}."""
        p_info = self.catalog.get(provider_name)
        if not p_info:
            raise ValueError(f"Provider '{provider_name}' not found in catalog.")

        key = self.get_api_key(provider_name, custom_key)
        is_keyless = p_info.get("isKeyless", False)

        if not key and not is_keyless:
            raise ValueError(f"Missing API key for {provider_name}. Enter your API key in the studio.")

        base_url = p_info.get("baseUrl") or "https://api.openai.com/v1"
        url, headers, _ = self.resolve_endpoint_and_headers(provider_name, base_url, model_id, key)

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": bool(on_chunk),
        }

        start_time = time.time()

        if on_chunk:
            # Streaming mode
            try:
                resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    err_msg = resp.text[:400]
                    raise RuntimeError(f"LLM API error (HTTP {resp.status_code}): {err_msg}")

                full_content = []
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_part = line_str[6:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_part)
                            delta = ""
                            if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                delta = chunk_json["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                full_content.append(delta)
                                on_chunk(delta)
                        except Exception:
                            continue

                elapsed_ms = int((time.time() - start_time) * 1000)
                final_text = "".join(full_content)
                return {
                    "content": final_text,
                    "latency_ms": elapsed_ms,
                    "provider": provider_name,
                    "model": model_id,
                }
            except Exception as e:
                # If streaming fails, retry non-streaming
                pass

        # Non-streaming call
        payload["stream"] = False
        resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if resp.status_code != 200:
            err_msg = resp.text[:400]
            raise RuntimeError(f"LLM API error (HTTP {resp.status_code}): {err_msg}")

        data = resp.json()
        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
        elif "message" in data:
            content = data["message"].get("content", "")

        return {
            "content": content.strip(),
            "latency_ms": elapsed_ms,
            "provider": provider_name,
            "model": model_id,
        }


# Global client singleton
client = LLMClient()
