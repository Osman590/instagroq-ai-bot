# groq_client.py
from typing import Any, Dict
from groq import Groq

# ---------- HELPERS: language/style/persona ----------
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
        return "Tone: friendly, lively, can joke a little. Use appropriate emojis sometimes. Do NOT be repetitive."
    if persona == "strict":
        return "Tone: businesslike and direct. Minimal emojis. If unclear, ask ONE clarifying question."
    if persona == "smart":
        return "Tone: smart and structured, but not dry. Use terms only if needed."
    return "Tone: warm, human, supportive. Occasional appropriate emojis."

def build_system_prompt(lang: str, style: str, persona: str) -> str:
    lang_code = normalize_lang(lang)
    lang_name = LANG_NAMES.get(lang_code, "Russian")

    return (
        "You are a helpful, natural-sounding chat assistant.\n"
        "Write like a real person in a messaging app.\n"
        "Do NOT start every reply with greetings.\n"
        "Do NOT use the user's name unless the user explicitly gave it in this chat.\n"
        "Avoid шаблонные фразы and repeating yourself.\n"
        "If info is missing, ask ONE clear question.\n"
        "Never mention system prompts or policies.\n"
        f"IMPORTANT: Always reply in {lang_name}, regardless of the language of previous messages.\n"
        f"{persona_rule(persona)}\n"
        f"{style_rule(style)}\n"
    )


# ---------- GROQ WRAPPER ----------
class GroqChat:
    def __init__(self, api_key: str, model: str):
        self.client = Groq(api_key=api_key)
        self.model = model

    def ask(
        self,
        text: str,
        lang: str = "ru",
        style: str = "steps",
        persona: str = "friendly",
        max_tokens: int = 600,
    ) -> str:
        system_prompt = build_system_prompt(lang, style, persona)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.95,
                top_p=0.9,
                frequency_penalty=0.35,
                presence_penalty=0.25,
                max_tokens=max_tokens,
            )
        except TypeError:
            # fallback для старых SDK
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.95,
                top_p=0.9,
                max_tokens=max_tokens,
            )

        return (resp.choices[0].message.content or "").strip()