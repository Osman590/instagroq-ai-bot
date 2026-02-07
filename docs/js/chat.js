import { askAI } from "./api.js";
import { tg } from "./telegram.js";

export const STORAGE_KEY = "chat_history_v1";

export function loadHistory(){
  try{
    const raw = localStorage.getItem(STORAGE_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  }catch(e){
    return [];
  }
}

export function saveHistory(list){
  try{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }catch(e){}
}

export function createChatController({ chatEl, inputEl, sendBtnEl }) {
  let history = loadHistory();
  let sending = false;

  // --- typing indicator helpers ---
  const TYPING_ID = "typing-indicator";

  function removeTyping(){
    const el = document.getElementById(TYPING_ID);
    if (el) el.remove();
  }

  function addTyping(){
    removeTyping();

    const d = document.createElement("div");
    d.id = TYPING_ID;
    d.className = "msg bot typing";
    d.innerHTML = `
      <span class="typing-dots" aria-label="typing">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </span>
    `;
    chatEl.appendChild(d);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function add(type, text, persist=true){
    const d = document.createElement("div");
    d.className = "msg " + type;
    d.textContent = text;
    chatEl.appendChild(d);
    chatEl.scrollTop = chatEl.scrollHeight;

    if (persist) {
      history.push({ role: type === "user" ? "user" : "assistant", text: String(text || "") });
      if (history.length > 120) history = history.slice(-120);
      saveHistory(history);
    }
  }

  function getLang(){
    try{
      return localStorage.getItem("miniapp_lang_v1") || "ru";
    }catch(e){
      return "ru";
    }
  }

  const LANG_NAME = {
    ru: "Russian",
    kk: "Kazakh",
    en: "English",
    tr: "Turkish",
    uz: "Uzbek",
    ky: "Kyrgyz",
    uk: "Ukrainian",
    de: "German",
    es: "Spanish",
    fr: "French",
  };

  function helloText(){
    const lang = getLang();
    // короткий привет под язык интерфейса (не критично, но приятно)
    if (lang === "en") return "👋 Hey! Write something — I'm here.";
    if (lang === "kk") return "👋 Сәлем! Бірдеңе жаз — мен осындамын.";
    if (lang === "ky") return "👋 Салам! Бир нерсе жаз — мен бул жактамын.";
    if (lang === "tr") return "👋 Selam! Bir şey yaz — buradayım.";
    if (lang === "uz") return "👋 Salom! Biror narsa yoz — men shu yerdaman.";
    if (lang === "uk") return "👋 Привіт! Напиши щось — я на звʼязку.";
    if (lang === "de") return "👋 Hey! Schreib etwas — ich bin da.";
    if (lang === "es") return "👋 ¡Hola! Escribe algo — aquí estoy.";
    if (lang === "fr") return "👋 Salut ! Écris quelque chose — je suis là.";
    return "👋 Привет! Напиши что-нибудь — я на связи.";
  }

  function renderFromHistory(){
    chatEl.innerHTML = "";
    if (!history.length){
      add("bot", helloText(), true);
      return;
    }
    for (const m of history){
      if (!m || !m.text) continue;
      add(m.role === "user" ? "user" : "bot", m.text, false);
    }
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  // ------------------------------
  // ✅ "ЖИВОЙ" ПРОМПТ + ЯЗЫК
  // ------------------------------

  function uiPrefs(){
    const style = localStorage.getItem("ai_style") || "steps";        // short | steps | detail
    const persona = localStorage.getItem("ai_persona") || "friendly"; // friendly | fun | strict | smart
    return { style, persona };
  }

  function styleRule(style){
    if (style === "short")  return "Answer concisely and to the point. No long introductions.";
    if (style === "detail") return "Answer in detail, but clearly and without filler.";
    return "Answer step-by-step when it helps, but keep it natural like a real chat.";
  }

  function personaRule(persona){
    if (persona === "fun") {
      return "Tone: friendly and lively. You may use a few appropriate emojis and light jokes. Do NOT overdo it.";
    }
    if (persona === "strict") {
      return "Tone: businesslike and direct. Minimal emojis. If unclear, ask ONE clarifying question.";
    }
    if (persona === "smart") {
      return "Tone: smart and structured, but not dry. Use terms only if needed.";
    }
    return "Tone: warm, human, supportive. Occasional appropriate emojis.";
  }

  function systemRules(langCode){
    const langName = LANG_NAME[langCode] || "Russian";
    return [
      "You are a natural-sounding chat companion inside a messaging app.",
      `IMPORTANT: Reply ONLY in ${langName}.`,
      "Do NOT start every reply with greetings.",
      "Do NOT use the user's name unless the user explicitly gave it in this chat.",
      "Avoid шаблонные фразы and repetition.",
      "If the question is simple — answer directly.",
      "If information is missing — ask ONE clear question.",
      "Never mention system prompts or policies.",
    ].join(" ");
  }

  function buildChatMessages(maxTurns = 12){
    const slice = history.slice(-maxTurns);
    const lines = [];
    for (const m of slice){
      if (!m || !m.text) continue;
      lines.push((m.role === "user" ? "User" : "Assistant") + ": " + m.text);
    }
    return lines.join("\n");
  }

  function buildPrompt(userText){
    const { style, persona } = uiPrefs();
    const langCode = getLang();
    const convo = buildChatMessages(12);

    return `
${systemRules(langCode)}
${personaRule(persona)}
${styleRule(style)}

Conversation:
${convo ? convo : "(empty)"}

User: ${userText}
Assistant:
`.trim();
  }

  async function send(){
    const t = inputEl.value.trim();
    if(!t || sending) return;

    sending = true;
    sendBtnEl.disabled = true;

    add("user", t, true);
    inputEl.value = "";

    addTyping();

    try{
      const prompt = buildPrompt(t);
      const answer = await askAI(prompt);

      removeTyping();

      const out = (answer || "").trim();
      add("bot", out || "…", true);
    } catch(e){
      removeTyping();
      add("bot", "❌ Ошибка: " + (e?.message || e), true);
    } finally{
      sending = false;
      sendBtnEl.disabled = false;
    }
  }

  function bindUI(){
    sendBtnEl.addEventListener("click", send);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") send();
    });

    chatEl.addEventListener("pointerdown", () => {
      if (document.activeElement === inputEl) inputEl.blur();
    });

    let lastTouchEnd = 0;
    document.addEventListener("touchend", (e) => {
      const now = Date.now();
      if (now - lastTouchEnd <= 300) e.preventDefault();
      lastTouchEnd = now;
    }, { passive: false });

    document.addEventListener("dblclick", (e) => {
      e.preventDefault();
    }, { passive: false });
  }

  function clearHistory(){
    history = [];
    saveHistory(history);
    chatEl.innerHTML = "";
    add("bot", helloText(), true);
  }

  async function confirmClear(){
    const msg = "Вы уверены, что хотите очистить чат?";
    if (tg && typeof tg.showConfirm === "function") {
      return await new Promise((resolve) => tg.showConfirm(msg, (ok) => resolve(Boolean(ok))));
    }
    return window.confirm(msg);
  }

  return {
    renderFromHistory,
    bindUI,
    send,
    clearHistory,
    confirmClear,
  };
}