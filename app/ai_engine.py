# app/ai_engine.py
"""
AI Engine - supports Anthropic Claude and Google Gemini API keys.
Auto-detects key type from prefix.
"""
import os
import json
import urllib.request
import urllib.error


def _call_anthropic(api_key: str, prompt: str) -> dict:
    """Call Anthropic Claude API"""
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


def _call_gemini(api_key: str, prompt: str) -> str:
    """Call Google Gemini REST API directly"""
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
    """Parse JSON from AI response, stripping any markdown fences"""
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        # Find the JSON block
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break
    return json.loads(text)


def generate_study_materials(content_text: str, options: list) -> dict:
    # Resolve API key — check all env vars
    api_key = (
        os.getenv("ANTHROPIC_API_KEY") or
        os.getenv("GEMINI_API_KEY") or
        os.getenv("OPENAI_API_KEY") or
        ""
    ).strip()

    if not api_key or api_key in ("your_gemini_api_key_here", "your_anthropic_api_key_here"):
        return {
            "error": (
                "No valid API key configured. "
                "Set ANTHROPIC_API_KEY (starts with sk-ant-) or "
                "GEMINI_API_KEY (starts with AIza) in your .env file."
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

    try:
        # Auto-detect key type
        if api_key.startswith("sk-ant-") or api_key.startswith("sk-"):
            raw = _call_anthropic(api_key, prompt)
        else:
            # Try Gemini (AIza... keys or other)
            raw = _call_gemini(api_key, prompt)

        return _parse_json_response(raw)

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", err_body[:200])
        except Exception:
            msg = err_body[:200]
        return {"error": f"API error {e.code}: {msg}"}
    except json.JSONDecodeError as e:
        return {"error": f"AI returned malformed JSON. Please try again. Details: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
