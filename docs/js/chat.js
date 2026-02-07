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

  function renderFromHistory(){
    chatEl.innerHTML = "";
    if (!history.length){
      add("bot", "👋 Привет! Напиши что-нибудь — я на связи.", true);
      return;
    }
    for (const m of history){
      if (!m || !m.text) continue;
      add(m.role === "user" ? "user" : "bot", m.text, false);
    }
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  // ------------------------------
  // ✅ ЛОГИКА "ЖИВОГО" ПРОМПТА
  // ------------------------------

  function uiPrefs(){
    const style = localStorage.getItem("ai_style") || "steps";     // short | steps | detail
    const persona = localStorage.getItem("ai_persona") || "friendly"; // friendly | fun | strict | smart
    return { style, persona };
  }

  function styleRule(style){
    if (style === "short")  return "Отвечай коротко и по делу. Без лишних вступлений.";
    if (style === "detail") return "Отвечай подробно, но живо и понятно. Без воды.";
    return "Отвечай по шагам, но естественно, как в переписке. Без занудства.";
  }

  function personaRule(persona){
    if (persona === "fun") {
      return "Стиль общения: дружелюбно и живо, можно немного шуток и уместные эмодзи. Не переигрывай.";
    }
    if (persona === "strict") {
      return "Стиль общения: деловой и прямой. Минимум эмодзи. Если не понял — задай 1 уточняющий вопрос.";
    }
    if (persona === "smart") {
      return "Стиль общения: умно и структурно, но без канцелярита. Термины — только если реально нужны.";
    }
    return "Стиль общения: тёплый, нормальный человеческий тон. Уместные эмодзи иногда.";
  }

  function buildChatMessages(maxTurns = 12){
    // ⚠️ Важно: не делаем "Пользователь/Ассистент:" как у протокола.
    // Делаем нормальный диалог, чтобы модель не уходила в шаблоны.
    const slice = history.slice(-maxTurns);
    const lines = [];
    for (const m of slice){
      if (!m || !m.text) continue;
      lines.push((m.role === "user" ? "User" : "Assistant") + ": " + m.text);
    }
    return lines.join("\n");
  }

  function systemRules(){
    // ✅ ДОБАВЛЕНО: язык + живость + меньше шаблонов (остальное не трогаем)
    return [
      "Ты — живой собеседник в чате. Пиши естественно.",
      "Всегда отвечай на том же языке, на котором написал пользователь в последнем сообщении. Если пользователь переключил язык — переключись тоже.",
      "НЕ начинай каждый ответ с приветствия.",
      "НЕ используй имя пользователя, если он сам не представился в этой переписке.",
      "НЕ повторяй одно и то же разными словами.",
      "Если вопрос простой — отвечай сразу. Не задавай лишние вопросы.",
      "Если информации не хватает — задай ОДИН нормальный уточняющий вопрос.",
      "Эмодзи: если persona='fun' — можно чаще и живее; иначе — редко и только уместно.",
      "Не говори фразы типа: «как ИИ», «я не настоящий» и т.п.",
      "Не будь токсичным и не груби.",
    ].join(" ");
  }

  function buildPrompt(userText){
    const { style, persona } = uiPrefs();

    const convo = buildChatMessages(12);
    // Конструкция без "Контекст диалога (запомни...)" — это тоже вызывало шаблонность.
    return `
${systemRules()}
Текущие настройки пользователя: persona=${persona}; style=${style}.
${personaRule(persona)}
${styleRule(style)}

Диалог:
${convo ? convo : "(диалог пустой)"}

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

    // ✅ typing
    addTyping();

    try{
      const prompt = buildPrompt(t);
      const answer = await askAI(prompt);

      removeTyping();

      // ✅ если модель вернула пусто — нормально обработаем
      const out = (answer || "").trim();
      add("bot", out || "Хмм… я не получил ответ. Попробуй ещё раз 🙂", true);
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
    add("bot", "👋 Привет! Напиши что-нибудь — я на связи.", true);
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