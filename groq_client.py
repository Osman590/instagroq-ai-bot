import os
from typing import Dict, Any
from groq import Groq

# ---------- ENV ----------
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ---------- language / style ----------
LANG_NAMES = {
    "ru": "Russian",
    "kk": "Kazakh",
    "en": "English",
    "tr": "Turkish",
    "uz": "Uzbek",
    "ky": "Kyrgyz",
    "uk": "Ukrainian",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
}

def normalize_lang(code: str) -> str:
    code = (code or "").strip().lower()
    return code if code in LANG_NAMES else "ru"

def style_rule(style: str) -> str:
    style = (style or "").strip().lower()
    if style == "short":
        return "Answer concisely and to the point. No long introductions."
    if style == "detail":
        return "Answer in detail, but clearly and without filler."
    return "Answer step-by-step when useful, but keep it natural like a real chat."

def persona_rule(persona: str) -> str:
    persona = (persona or "").strip().lower()
    if persona == "fun":
        return "Tone: friendly, lively, can joke a little. Use appropriate emojis sometimes."
    if persona == "strict":
        return "Tone: businesslike and direct. Minimal emojis."
    if persona == "smart":
        return "Tone: smart and structured, but not dry."
    return "Tone: warm, human, supportive."

def build_system_prompt(lang: str, style: str, persona: str) -> str:
    lang_code = normalize_lang(lang)
    lang_name = LANG_NAMES.get(lang_code, "Russian")

    return (
        "You are a helpful, natural-sounding chat assistant.\n"
        "Write like a real person in a messaging app.\n"
        "Do NOT start every reply with greetings.\n"
        "Avoid repeating yourself.\n"
        f"IMPORTANT: Always reply in {lang_name}.\n"
        f"{persona_rule(persona)}\n"
        f"{style_rule(style)}\n"
    )

def ask_groq(text: str, lang: str, style: str, persona: str) -> str:
    if not groq_client:
        raise RuntimeError("GROQ_API_KEY is not set")

    system_prompt = build_system_prompt(lang, style, persona)

    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.95,
        top_p=0.9,
        frequency_penalty=0.35,
        presence_penalty=0.25,
        max_tokens=600,
    )

    return (resp.choices[0].message.content or "").strip()