const tg = window.Telegram?.WebApp;

// ===== VH (Telegram/iOS) =====
function applyVH(){
  if (tg && typeof tg.viewportHeight === "number") {
    document.documentElement.style.setProperty("--vh", tg.viewportHeight + "px");
  } else {
    document.documentElement.style.setProperty("--vh", window.innerHeight + "px");
  }
}

if (tg) {
  tg.ready();
  tg.expand();
  applyVH();
  tg.onEvent("viewportChanged", applyVH);
} else {
  applyVH();
  window.addEventListener("resize", applyVH);
}

// ===== language =====
const STORAGE_LANG = "miniapp_lang_v1";

const chatBtn = document.getElementById("chatBtn");
const subText = document.getElementById("subText");
const verText = document.getElementById("verText");
const langTitle = document.getElementById("langTitle");

const langBtn = document.getElementById("langBtn");
const langOverlay = document.getElementById("langOverlay");
const langList = document.getElementById("langList");
const langClose = document.getElementById("langClose");
const langSheetTitle = document.getElementById("langSheetTitle");

const I18N = {
  ru: { btn:"Чат с ИИ", sub:"Быстрые ответы • Память • Заметки", ver:"miniapp v2", lang:"Язык интерфейса", sheet:"Язык" },
  kk: { btn:"AI чат", sub:"Жылдам жауаптар • Есте сақтау • Жазбалар", ver:"miniapp v2", lang:"Тіл", sheet:"Тіл" },
  en: { btn:"AI Chat", sub:"Fast replies • Memory • Notes", ver:"miniapp v2", lang:"Language", sheet:"Language" },
  tr: { btn:"Yapay Zekâ Sohbet", sub:"Hızlı yanıtlar • Hafıza • Notlar", ver:"miniapp v2", lang:"Dil", sheet:"Dil" },
  uz: { btn:"AI Chat", sub:"Tez javoblar • Xotira • Eslatmalar", ver:"miniapp v2", lang:"Til", sheet:"Til" },
  ky: { btn:"AI чат", sub:"Тез жооптор • Эс тутум • Жазмалар", ver:"miniapp v2", lang:"Тил", sheet:"Тил" },
  uk: { btn:"AI чат", sub:"Швидкі відповіді • Пам’ять • Нотатки", ver:"miniapp v2", lang:"Мова", sheet:"Мова" },
  de: { btn:"KI-Chat", sub:"Schnelle Antworten • Speicher • Notizen", ver:"miniapp v2", lang:"Sprache", sheet:"Sprache" },
  es: { btn:"Chat IA", sub:"Respuestas rápidas • Memoria • Notas", ver:"miniapp v2", lang:"Idioma", sheet:"Idioma" },
  fr: { btn:"Chat IA", sub:"Réponses rapides • Mémoire • Notes", ver:"miniapp v2", lang:"Langue", sheet:"Langue" },
};

const LANGS = [
  { code:"ru", label:"Русский (RU)" },
  { code:"kk", label:"Қазақша (KZ)" },
  { code:"en", label:"English (EN)" },
  { code:"tr", label:"Türkçe (TR)" },
  { code:"uz", label:"O‘zbek (UZ)" },
  { code:"ky", label:"Кыргызча (KG)" },
  { code:"uk", label:"Українська (UA)" },
  { code:"de", label:"Deutsch (DE)" },
  { code:"es", label:"Español (ES)" },
  { code:"fr", label:"Français (FR)" },
];

function getSavedLang(){
  try{ return localStorage.getItem(STORAGE_LANG) || "ru"; }
  catch(e){ return "ru"; }
}

function saveLang(lang){
  try{ localStorage.setItem(STORAGE_LANG, lang); }catch(e){}
}

function setLang(lang){
  const t = I18N[lang] || I18N.ru;

  chatBtn.textContent = t.btn;
  subText.textContent = t.sub;
  verText.textContent = t.ver;
  langTitle.textContent = t.lang;
  langSheetTitle.textContent = t.sheet;

  // pill text
  const found = LANGS.find(x => x.code === lang);
  langBtn.childNodes[0].nodeValue = (found ? found.label : "Русский (RU)") + " ";

  // pass lang to chat.html
  const baseHref = "./chat.html?v=2";
  chatBtn.href = baseHref + "&lang=" + encodeURIComponent(lang);

  // persist
  saveLang(lang);

  // update selected UI
  paintSelected(lang);
}

function paintSelected(lang){
  const items = langList.querySelectorAll(".langItem");
  items.forEach(btn => {
    const code = btn.getAttribute("data-lang");
    btn.classList.toggle("selected", code === lang);
  });
}

function openLang(){
  langOverlay.classList.add("show");
  langOverlay.setAttribute("aria-hidden", "false");
  langBtn.setAttribute("aria-expanded", "true");
}

function closeLang(){
  langOverlay.classList.remove("show");
  langOverlay.setAttribute("aria-hidden", "true");
  langBtn.setAttribute("aria-expanded", "false");
}

// build list once
function buildLangList(){
  langList.innerHTML = "";
  for (const x of LANGS){
    const b = document.createElement("button");
    b.type = "button";
    b.className = "langItem";
    b.setAttribute("data-lang", x.code);
    b.innerHTML = `<span>${x.label}</span><span class="check">✓</span>`;
    b.addEventListener("click", () => {
      setLang(x.code);
      closeLang();
    });
    langList.appendChild(b);
  }
}

buildLangList();
setLang(getSavedLang());

// open/close handlers
langBtn.addEventListener("click", openLang);
langClose.addEventListener("click", closeLang);

// click outside sheet closes
langOverlay.addEventListener("click", (e) => {
  if (e.target === langOverlay) closeLang();
});

// ESC (если откроют в браузере)
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeLang();
});