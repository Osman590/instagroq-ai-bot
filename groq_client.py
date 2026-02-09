def ask_groq_chat(
    messages: list,
    *,
    lang: str = "ru",
    style: str = "steps",
    persona: str = "friendly",
) -> str:
    """
    messages: [{"role":"user"/"assistant", "content":"..."}]
    """
    if not groq_client:
        raise RuntimeError("GROQ_API_KEY is not set")

    system_prompt = build_system_prompt(lang, style, persona)

    payload = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            payload.append({"role": role, "content": content})

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=payload,
            temperature=0.95,
            top_p=0.9,
            frequency_penalty=0.35,
            presence_penalty=0.25,
            max_tokens=600,
        )
    except TypeError:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=payload,
            temperature=0.95,
            top_p=0.9,
            max_tokens=600,
        )

    return (resp.choices[0].message.content or "").strip()