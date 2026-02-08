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
    tg_user_id: u.id,
    tg_username: u.username || null,
    tg_first_name: u.first_name || null,
  };
}

export async function askAI(promptText) {
  const user = getTelegramUser();

  const payload = {
    text: promptText,
    lang: getLang(),
    style: getStyle(),
    persona: getPersona(),

    // ✅ ИМЕННО ТАК ЖДЁТ api.py
    tg_user_id: user.tg_user_id,
    tg_username: user.tg_username,
    tg_first_name: user.tg_first_name,
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