// docs/js/image-api.js

const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_IMAGE = API_BASE + "/api/image";

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

export async function generateImage({ prompt, mode, file }) {
  const user = getTelegramUser();

  const form = new FormData();
  form.append("prompt", String(prompt || ""));
  form.append("mode", String(mode || ""));
  form.append("tg_user_id", String(user.tg_user_id || ""));
  form.append("tg_username", String(user.tg_username || ""));
  form.append("tg_first_name", String(user.tg_first_name || ""));

  if (file) form.append("image", file);

  const r = await fetch(API_IMAGE, {
    method: "POST",
    body: form,
  });

  if (!r.ok) {
    throw new Error("API error " + r.status);
  }

  return await r.json();
}