# app/ai_engine.py
"""
AI Engine for StudyOS Content Cruncher.
Primary provider: NVIDIA NIM (OpenAI-compatible endpoint, free-tier friendly).
Falls back to Anthropic Claude or Google Gemini if those keys are configured instead.
"""
import os
import json
import urllib.request
import urllib.error


# ── NVIDIA NIM (OpenAI-compatible) ───────────────────────────────────────────
def _call_nvidia(api_key: str, prompt: str) -> str:
    """Call NVIDIA NIM chat-completions endpoint (OpenAI-compatible REST API)."""
    payload = json.dumps({
        "model": "meta/llama-3.1-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 4000,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()


# ── Anthropic Claude (fallback) ──────────────────────────────────────────────
def _call_anthropic(api_key: str, prompt: str) -> str:
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return body["content"][0]["text"].strip()


# ── Google Gemini (fallback) ─────────────────────────────────────────────────
def _call_gemini(api_key: str, prompt: str) -> str:
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from AI response, stripping any markdown fences."""
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break
    # Trim anything before the first '{' in case the model added stray preamble text
    if "{" in text and not text.strip().startswith("{"):
        text = text[text.index("{"):]
    return json.loads(text)


def generate_study_materials(content_text: str, options: list) -> dict:
    """
    Generate study materials (summary / flashcards / quiz / mind map) from content_text.
    Tries NVIDIA NIM first (NVIDIA_API_KEY), then falls back to Anthropic or Gemini
    if those keys are set instead.
    """
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not any([nvidia_key, anthropic_key, gemini_key]):
        return {
            "error": (
                "No valid API key configured. "
                "Set NVIDIA_API_KEY (starts with nvapi-), ANTHROPIC_API_KEY (starts with sk-ant-) "
                "or GEMINI_API_KEY in your .env file."
            )
        }

    options = [opt.lower().strip() for opt in options]
    requests_list = []

    if "summary" in options:
        requests_list.append('- "summary" (string): A comprehensive 3-5 paragraph summary')
    if "flashcards" in options:
        requests_list.append('- "flashcards" (array of objects): Each object has "question" and "answer" strings. Generate at least 8.')
    if "quiz" in options:
        requests_list.append('- "quiz_questions" (array of objects): Each object has "question" (string), "options" (array of 4 strings), "correct_answer" (string). Generate at least 5.')
    if "mind map" in options or "mindmap" in options:
        requests_list.append('- "mind_map" (nested object): Hierarchical structure of core concepts.')

    if not requests_list:
        return {"error": "No valid options selected for generation."}

    request_str = "\n".join(requests_list)

    prompt = f"""You are an expert academic tutor. Analyze the following educational content and generate the requested study materials.

CRITICAL: Respond ONLY with a valid JSON object. No markdown code fences, no preamble, no explanation — ONLY the raw JSON object.

The JSON must contain these keys:
{request_str}

CONTENT:
{content_text[:25000]}"""

    # Try providers in order of preference: NVIDIA -> Anthropic -> Gemini
    last_error = None

    if nvidia_key:
        try:
            raw = _call_nvidia(nvidia_key, prompt)
            return _parse_json_response(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_error = f"NVIDIA API error {e.code}: {err_body[:300]}"
        except json.JSONDecodeError as e:
            last_error = f"NVIDIA returned malformed JSON: {str(e)}"
        except Exception as e:
            last_error = f"NVIDIA API error: {str(e)}"

    if anthropic_key:
        try:
            raw = _call_anthropic(anthropic_key, prompt)
            return _parse_json_response(raw)
        except Exception as e:
            last_error = f"Anthropic API error: {str(e)}"

    if gemini_key:
        try:
            raw = _call_gemini(gemini_key, prompt)
            return _parse_json_response(raw)
        except Exception as e:
            last_error = f"Gemini API error: {str(e)}"

    return {"error": last_error or "All configured AI providers failed."}
