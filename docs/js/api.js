// app.js

const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_CHAT = API_BASE + "/api/chat";

function getLang(){
  return localStorage.getItem("miniapp_lang_v1") || "ru";
}

function getStyle(){
  return localStorage.getItem("ai_style") || "steps";
}

function getPersona(){
  return localStorage.getItem("ai_persona") || "friendly";
}

// ✅ Telegram user
function getTelegramUser(){
  const tg = window.Telegram?.WebApp;
  if (!tg || !tg.initDataUnsafe?.user) return {};

  const u = tg.initDataUnsafe.user;
  return {
    tg_user_id: u.id,
    tg_username: u.username || "—",
    tg_first_name: u.first_name || "—",
  };
}

export async function askAI(promptText) {
  const user = getTelegramUser();

  const payload = {
    text: promptText,
    lang: getLang(),
    style: getStyle(),
    persona: getPersona(),

    // 🔥 ВАЖНО — имена как в api.py
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
    throw new Error("API error " + r.status);
  }

  const data = await r.json();
  return (data.reply || "").trim();
}