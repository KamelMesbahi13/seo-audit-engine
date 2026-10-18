"""Provider Catalog for Free LLM APIs.

Loads and parses data.json from awesome-free-llm-apis.
Provides provider metadata, model lists, API key environment variable mappings,
and endpoint configurations.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_JSON_CANDIDATES = [
    CURRENT_DIR / "data.json",
    PROJECT_ROOT / "llm" / "data.json",
    Path("C:/Users/EL ASSLI HI TECH/Documents/awesome-free-llm-apis-main/awesome-free-llm-apis-main/data.json"),
    Path("C:/Users/EL ASSLI HI TECH/Documents/awesome-free-llm-apis-main/data.json"),
]

# Environment variable keys for providers
PROVIDER_ENV_KEYS: Dict[str, str] = {
    "Aion Labs": "AION_API_KEY",
    "Cohere": "COHERE_API_KEY",
    "Google Gemini": "GEMINI_API_KEY",
    "Mistral AI": "MISTRAL_API_KEY",
    "Z AI (Zhipu AI)": "ZAI_API_KEY",
    "Cloudflare Workers AI": "CF_API_TOKEN",
    "Groq": "GROQ_API_KEY",
    "Hugging Face": "HF_API_KEY",
    "Kilo Code": "KILO_API_KEY",
    "LLM7.io": "LLM7_API_KEY",
    "ModelScope": "MODELSCOPE_API_KEY",
    "NVIDIA NIM": "NVIDIA_API_KEY",
    "Ollama Cloud": "OLLAMA_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "OVHcloud AI Endpoints": "OVH_API_KEY",
    "SiliconFlow": "SILICONFLOW_API_KEY"
}

# Special endpoint types
PROVIDER_TYPES: Dict[str, str] = {
    "Google Gemini": "gemini",
    "Cohere": "cohere",
    "Cloudflare Workers AI": "cloudflare",
    "Ollama Cloud": "ollama",
    "LLM7.io": "keyless",
    "OVHcloud AI Endpoints": "keyless",
}

# Extra popular / verified free models to augment catalog if missing
ADDITIONAL_POPULAR_MODELS: Dict[str, List[Dict[str, Any]]] = {
    "Groq": [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "context": "128K", "maxOutput": "32K", "modality": "Text", "rateLimit": "30 RPM (Free)"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "context": "128K", "maxOutput": "8K", "modality": "Text", "rateLimit": "30 RPM (Free)"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": "32K", "maxOutput": "32K", "modality": "Text", "rateLimit": "30 RPM (Free)"},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B IT", "context": "8K", "maxOutput": "8K", "modality": "Text", "rateLimit": "30 RPM (Free)"},
    ],
    "Google Gemini": [
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Fast & Accurate)", "context": "1M", "maxOutput": "8K", "modality": "Multimodal", "rateLimit": "15 RPM (Free)"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context": "1M", "maxOutput": "8K", "modality": "Multimodal", "rateLimit": "15 RPM (Free)"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context": "2M", "maxOutput": "8K", "modality": "Multimodal", "rateLimit": "2 RPM (Free)"},
    ],
    "OpenRouter": [
        {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B Instruct (Free)", "context": "128K", "maxOutput": "8K", "modality": "Text", "rateLimit": "20 RPD (Free)"},
        {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1 Reasoning (Free)", "context": "64K", "maxOutput": "8K", "modality": "Text (Reasoning)", "rateLimit": "20 RPD (Free)"},
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash Exp (Free)", "context": "1M", "maxOutput": "8K", "modality": "Multimodal", "rateLimit": "20 RPD (Free)"},
        {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B Instruct (Free)", "context": "32K", "maxOutput": "4K", "modality": "Text", "rateLimit": "20 RPD (Free)"},
    ],
    "Mistral AI": [
        {"id": "mistral-small-latest", "name": "Mistral Small Latest", "context": "32K", "maxOutput": "8K", "modality": "Text", "rateLimit": "1 RPS (Free)"},
        {"id": "open-mistral-7b", "name": "Open Mistral 7B", "context": "32K", "maxOutput": "8K", "modality": "Text", "rateLimit": "1 RPS (Free)"},
    ],
}


def load_raw_catalog() -> Dict[str, Any]:
    """Loads raw data.json from candidates."""
    for p in DATA_JSON_CANDIDATES:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    # Minimal fallback catalog
    return {
        "providers": [
            {
                "name": "Groq",
                "category": "inference_provider",
                "country": "US",
                "flag": "🇺🇸",
                "url": "https://console.groq.com/keys",
                "baseUrl": "https://api.groq.com/openai/v1",
                "description": "Ultra-fast LPU inference, free tier with no credit card required.",
                "models": ADDITIONAL_POPULAR_MODELS["Groq"]
            },
            {
                "name": "Google Gemini",
                "category": "frontier_model",
                "country": "US",
                "flag": "🇺🇸",
                "url": "https://aistudio.google.com/app/apikey",
                "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
                "description": "15 RPM free tier with 1M-2M context window.",
                "models": ADDITIONAL_POPULAR_MODELS["Google Gemini"]
            },
            {
                "name": "OpenRouter",
                "category": "aggregator",
                "country": "US",
                "flag": "🇺🇸",
                "url": "https://openrouter.ai/keys",
                "baseUrl": "https://openrouter.ai/api/v1",
                "description": "Unified gateway to top free models (:free suffix).",
                "models": ADDITIONAL_POPULAR_MODELS["OpenRouter"]
            }
        ]
    }


class ProviderCatalog:
    """Manages LLM providers, models, and metadata."""

    def __init__(self):
        raw = load_raw_catalog()
        self.raw_providers: List[Dict[str, Any]] = raw.get("providers", [])
        self._provider_map: Dict[str, Dict[str, Any]] = {}
        self._processed_providers: List[Dict[str, Any]] = []

        self._process_catalog()

    def _process_catalog(self):
        for p in self.raw_providers:
            name = p.get("name", "").strip()
            if not name:
                continue

            models = []
            seen_ids = set()

            # Add extra popular models first if any
            if name in ADDITIONAL_POPULAR_MODELS:
                for em in ADDITIONAL_POPULAR_MODELS[name]:
                    mid = em["id"]
                    if mid not in seen_ids:
                        models.append(em)
                        seen_ids.add(mid)

            # Add models from data.json
            for m in p.get("models", []):
                if not m:
                    continue
                mid = m.get("id") or m.get("name")
                if mid and mid not in seen_ids:
                    models.append({
                        "id": mid,
                        "name": m.get("name") or mid,
                        "context": m.get("context", "32K"),
                        "maxOutput": m.get("maxOutput", "8K"),
                        "modality": m.get("modality", "Text"),
                        "rateLimit": m.get("rateLimit", "Free Tier")
                    })
                    seen_ids.add(mid)

            env_var = PROVIDER_ENV_KEYS.get(name, f"{name.upper().replace(' ', '_')}_KEY")
            p_type = PROVIDER_TYPES.get(name, "standard")
            is_keyless = p_type == "keyless" or "ovh" in name.lower() or "llm7" in name.lower()
            has_env_key = bool(os.getenv(env_var))

            item = {
                "name": name,
                "category": p.get("category", "inference_provider"),
                "country": p.get("country", ""),
                "flag": p.get("flag", "🌐"),
                "url": p.get("url", ""),
                "baseUrl": p.get("baseUrl", "").rstrip("/"),
                "description": p.get("description", ""),
                "envKey": env_var,
                "hasEnvKey": has_env_key,
                "isKeyless": is_keyless,
                "endpointType": p_type,
                "modelsCount": len(models),
                "models": models,
            }

            self._provider_map[name] = item
            self._processed_providers.append(item)

        # Sort so that top recommended free providers appear first
        priority_order = ["Groq", "Google Gemini", "OpenRouter", "Mistral AI", "OVHcloud AI Endpoints", "LLM7.io", "Hugging Face", "Cohere"]
        def sort_key(p):
            try:
                idx = priority_order.index(p["name"])
                return (0, idx)
            except ValueError:
                return (1, p["name"])

        self._processed_providers.sort(key=sort_key)

    def get_all(self) -> List[Dict[str, Any]]:
        return self._processed_providers

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self._provider_map.get(name)


# Global singleton instance
catalog = ProviderCatalog()
