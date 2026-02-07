// ✅ ВАЖНО: твой Railway домен (без / в конце)
const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_CHAT = API_BASE + "/api/chat";

export async function askAI(promptText) {
  const r = await fetch(API_CHAT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: promptText })
  });

  if (!r.ok) {
    const t = await r.text();
    throw new Error("API " + r.status + ": " + t);
  }

  const data = await r.json();
  return (data.reply || "").trim();
}