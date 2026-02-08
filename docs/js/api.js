// app.js

const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_CHAT = API_BASE + "/api/chat";

function getLang(){
  try{ return localStorage.getItem("miniapp_lang_v1") || "ru"; }
  catch(e){ return "ru"; }
}

function getStyle(){
  try{ return localStorage.getItem("ai_style") || "steps"; }
  catch(e){ return "steps"; }
}

function getPersona(){
  try{ return localStorage.getItem("ai_persona") || "friendly"; }
  catch(e){ return "friendly"; }
}

// ✅ получаем данные Telegram пользователя
function getTelegramUser(){
  const tg = window.Telegram?.WebApp;
  if (!tg || !tg.initDataUnsafe?.user) return {};

  const u = tg.initDataUnsafe.user;
  return {
    telegram_user_id: u.id,
    username: u.username || null,
  };
}

export async function askAI(promptText) {
  const user = getTelegramUser();

  const payload = {
    text: promptText,
    lang: getLang(),
    style: getStyle(),
    persona: getPersona(),

    // ✅ ВАЖНО
    telegram_user_id: user.telegram_user_id,
    username: user.username,
  };

  const r = await fetch(API_CHAT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!r.ok) {
    const t = await r.text();
    throw new Error("API " + r.status + ": " + t);
  }

  const data = await r.json();
  return (data.reply || "").trim();
}