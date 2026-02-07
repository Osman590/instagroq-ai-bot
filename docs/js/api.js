// ✅ ВАЖНО: твой Railway домен (без / в конце)
const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_CHAT = API_BASE + "/api/chat";

function getLang(){
  try{
    return localStorage.getItem("miniapp_lang_v1") || "ru";
  }catch(e){
    return "ru";
  }
}

function getStyle(){
  try{
    return localStorage.getItem("ai_style") || "steps";
  }catch(e){
    return "steps";
  }
}

function getPersona(){
  try{
    return localStorage.getItem("ai_persona") || "friendly";
  }catch(e){
    return "friendly";
  }
}

export async function askAI(promptText) {
  const payload = {
    text: promptText,
    lang: getLang(),
    style: getStyle(),
    persona: getPersona(),
  };

  const r = await fetch(API_CHAT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const t = await r.text();
    throw new Error("API " + r.status + ": " + t);
  }

  const data = await r.json();
  return (data.reply || "").trim();
}