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

  function renderFromHistory(){
    chatEl.innerHTML = "";
    if (!history.length){
      add("bot", "👋 Привет! Я ИИ. Напиши что-нибудь.", true);
      return;
    }
    for (const m of history){
      if (!m || !m.text) continue;
      add(m.role === "user" ? "user" : "bot", m.text, false);
    }
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function stylePrefix(){
    const style = localStorage.getItem("ai_style") || "steps";
    if (style === "short")  return "Ответь максимально кратко и по делу. ";
    if (style === "detail") return "Ответь подробно, с объяснениями. ";
    return "Ответь по шагам, но без воды. ";
  }

  function personaPrefix(){
    const persona = localStorage.getItem("ai_persona") || "friendly";

    if (persona === "fun") {
      return "Ты весёлый и очень дружелюбный собеседник. Пиши живо, добавляй уместные эмодзи 😄✨, можешь слегка шутить, но отвечай точно. Если человек грустит — поддержи и подбодри 💙. ";
    }
    if (persona === "strict") {
      return "Ты строгий, деловой ассистент. Минимум эмодзи (только если уместно), короткие формулировки, без болтовни. Если запрос непонятен — задай 1 уточняющий вопрос. ";
    }
    if (persona === "smart") {
      return "Ты умный аналитичный помощник. Объясняй ясно, структурно, можешь использовать термины, но без занудства. Уместные эмодзи редко 🧠. ";
    }
    return "Ты общительный, тёплый и заботливый помощник. Общайся естественно, добавляй уместные эмодзи 🙂💬. Если человек грустит — поддержи. ";
  }

  function buildContextText(maxTurns = 12){
    const slice = history.slice(-maxTurns);
    let out = "Контекст диалога (запомни и учитывай):\n";
    for (const m of slice){
      const who = m.role === "user" ? "Пользователь" : "Ассистент";
      out += `${who}: ${m.text}\n`;
    }
    out += "\nТеперь ответь на новое сообщение пользователя:\n";
    return out;
  }

  async function send(){
    const t = inputEl.value.trim();
    if(!t || sending) return;

    sending = true;
    sendBtnEl.disabled = true;

    add("user", t, true);
    inputEl.value = "";

    add("bot", "⌛ Думаю...", false);

    try{
      const prompt =
        personaPrefix() +
        stylePrefix() +
        buildContextText(12) +
        "Пользователь: " + t;

      const answer = await askAI(prompt);

      const last = chatEl.lastElementChild;
      if (last && last.classList.contains("msg") && last.classList.contains("bot") && last.textContent.includes("⌛")) {
        last.remove();
      }

      add("bot", answer || "⚠️ Пустой ответ от API.", true);
    } catch(e){
      const last = chatEl.lastElementChild;
      if (last && last.classList.contains("msg") && last.classList.contains("bot") && last.textContent.includes("⌛")) {
        last.remove();
      }
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

    // Закрытие клавиатуры при тапе по зоне чата
    chatEl.addEventListener("pointerdown", () => {
      if (document.activeElement === inputEl) inputEl.blur();
    });

    // Убираем double-tap zoom на iOS
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
    add("bot", "👋 Привет! Я ИИ. Напиши что-нибудь.", true);
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