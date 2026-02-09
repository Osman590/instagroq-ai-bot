import os
from typing import Optional

# ---------- ENV ----------
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()


# ---------- Language / Style / Persona ----------
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


def normalize_lang(code: Optional[str]) -> str:
    code = (code or "").strip().lower()
    return code if code in LANG_NAMES else "ru"


def style_rule(style: Optional[str]) -> str:
    style = (style or "").strip().lower()
    if style == "short":
        return "Answer concisely and to the point. No long introductions."
    if style == "detail":
        return "Answer in detail, but clearly and without filler."
    return "Answer step-by-step when useful, but keep it natural like a real chat."


def persona_rule(persona: Optional[str]) -> str:
    persona = (persona or "").strip().lower()
    if persona == "fun":
        return "Tone: friendly, lively, can joke a little. Use emojis sometimes."
    if persona == "strict":
        return "Tone: businesslike and direct. Minimal emojis."
    if persona == "smart":
        return "Tone: smart and structured, but not dry."
    return "Tone: warm, human, supportive."


def build_system_prompt(lang: str, style: str, persona: str) -> str:
    lang_code = normalize_lang(lang)
    lang_name = LANG_NAMES.get(lang_code, "Russian")

    return (
        "You are a helpful chat assistant.\n"
        "Write like a real person in a messaging app.\n"
        "Do NOT start every reply with greetings.\n"
        "Avoid шаблонные фразы.\n"
        "Ask ONE clarifying question if something is unclear.\n"
        f"IMPORTANT: Always reply in {lang_name}.\n"
        f"{persona_rule(persona)}\n"
        f"{style_rule(style)}\n"
    )


def _get_groq_client():
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")

    try:
        from groq import Groq
    except Exception as e:
        raise RuntimeError(f"Groq SDK is not available: {e}")

    return Groq(api_key=GROQ_API_KEY)


# ---------- MAIN AI FUNCTION ----------
def ask_groq(
    user_text: str,
    *,
    lang: str = "ru",
    style: str = "steps",
    persona: str = "friendly",
) -> str:
    client = _get_groq_client()
    system_prompt = build_system_prompt(lang, style, persona)

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.95,
            top_p=0.9,
            frequency_penalty=0.35,
            presence_penalty=0.25,
            max_tokens=600,
        )
    except TypeError:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.95,
            top_p=0.9,
            max_tokens=600,
        )

    return (resp.choices[0].message.content or "").strip()