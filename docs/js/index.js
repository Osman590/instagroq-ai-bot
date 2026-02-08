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

// ===== storage keys =====
const STORAGE_LANG = "miniapp_lang_v1";
const STORAGE_THEME = "miniapp_theme_v1";

// ===== DOM =====
const chatBtn = document.getElementById("chatBtn");
const subText = document.getElementById("subText");
const verText = document.getElementById("verText");
const langTitle = document.getElementById("langTitle");

const langBtn = document.getElementById("langBtn");
const langOverlay = document.getElementById("langOverlay");
const langList = document.getElementById("langList");
const langClose = document.getElementById("langClose");
const langSheetTitle = document.getElementById("langSheetTitle");

// ✅ theme UI
const themeBtn = document.getElementById("themeBtn");
const themeOverlay = document.getElementById("themeOverlay");
const themeList = document.getElementById("themeList");
const themeClose = document.getElementById("themeClose");
const themeSheetTitle = document.getElementById("themeSheetTitle");

// ===== helpers =====
function getSavedLang(){
  try{ return localStorage.getItem(STORAGE_LANG) || "ru"; }
  catch(e){ return "ru"; }
}
function saveLang(lang){
  try{ localStorage.setItem(STORAGE_LANG, lang); }catch(e){}
}

function getSavedTheme(){
  try{ return localStorage.getItem(STORAGE_THEME) || "blue"; }
  catch(e){ return "blue"; }
}
function saveTheme(theme){
  try{ localStorage.setItem(STORAGE_THEME, theme); }catch(e){}
}

function applyTheme(theme){
  document.documentElement.setAttribute("data-theme", theme || "blue");
}

/**
 * ✅ Безопасно меняет текст в кнопке, не трогая <span class="chev">
 * Работает даже если первый child — не текст.
 */
function setPillLabel(btn, text){
  if (!btn) return;

  // ищем первый текстовый узел
  let textNode = null;
  for (const n of btn.childNodes) {
    if (n && n.nodeType === Node.TEXT_NODE) { textNode = n; break; }
  }

  // если нет — создаём текстовый узел в начало
  if (!textNode) {
    textNode = document.createTextNode("");
    btn.insertBefore(textNode, btn.firstChild);
  }

  textNode.nodeValue = text + " ";
}

function setChatLink(lang, theme){
  if (!chatBtn) return;
  const baseHref = "./chat.html?v=2";
  chatBtn.href = baseHref
    + "&lang=" + encodeURIComponent(lang)
    + "&theme=" + encodeURIComponent(theme);
}

// ===== i18n =====
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

const THEMES = [
  { code:"blue", label:"Синий" },
  { code:"black", label:"Черный" },
  { code:"purple", label:"Фиолетовый" },
  { code:"green", label:"Зеленый" },
  { code:"gray", label:"Серый" },
];

function themeLabel(theme){
  const f = THEMES.find(x => x.code === theme);
  return f ? f.label : "Синий";
}

function paintSelectedLang(lang){
  if (!langList) return;
  const items = langList.querySelectorAll(".langItem");
  items.forEach(btn => {
    const code = btn.getAttribute("data-lang");
    btn.classList.toggle("selected", code === lang);
  });
}

function paintSelectedTheme(theme){
  if (!themeList) return;
  const items = themeList.querySelectorAll(".themeItem");
  items.forEach(btn => {
    const code = btn.getAttribute("data-theme");
    btn.classList.toggle("selected", code === theme);
  });
}

function setLang(lang){
  const t = I18N[lang] || I18N.ru;

  if (chatBtn) chatBtn.textContent = t.btn;
  if (subText) subText.textContent = t.sub;
  if (verText) verText.textContent = t.ver;
  if (langTitle) langTitle.textContent = t.lang;
  if (langSheetTitle) langSheetTitle.textContent = t.sheet;

  const found = LANGS.find(x => x.code === lang);
  setPillLabel(langBtn, found ? found.label : "Русский (RU)");

  saveLang(lang);
  paintSelectedLang(lang);

  setChatLink(lang, getSavedTheme());
}

function setTheme(theme){
  applyTheme(theme);
  saveTheme(theme);
  paintSelectedTheme(theme);

  setPillLabel(themeBtn, "Цвет: " + themeLabel(theme));

  setChatLink(getSavedLang(), theme);
}

// ===== overlays =====
function openLang(){
  if (!langOverlay || !langBtn) return;
  langOverlay.classList.add("show");
  langOverlay.setAttribute("aria-hidden", "false");
  langBtn.setAttribute("aria-expanded", "true");
}
function closeLang(){
  if (!langOverlay || !langBtn) return;
  langOverlay.classList.remove("show");
  langOverlay.setAttribute("aria-hidden", "true");
  langBtn.setAttribute("aria-expanded", "false");
}

function openTheme(){
  if (!themeOverlay || !themeBtn) return;
  themeOverlay.classList.add("show");
  themeOverlay.setAttribute("aria-hidden", "false");
  themeBtn.setAttribute("aria-expanded", "true");
}
function closeTheme(){
  if (!themeOverlay || !themeBtn) return;
  themeOverlay.classList.remove("show");
  themeOverlay.setAttribute("aria-hidden", "true");
  themeBtn.setAttribute("aria-expanded", "false");
}

function buildLangList(){
  if (!langList) return;
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

function buildThemeList(){
  if (!themeList) return;
  themeList.innerHTML = "";
  for (const x of THEMES){
    const b = document.createElement("button");
    b.type = "button";
    b.className = "themeItem";
    b.setAttribute("data-theme", x.code);
    b.innerHTML = `<span>${x.label}</span><span class="check">✓</span>`;
    b.addEventListener("click", () => {
      setTheme(x.code);
      closeTheme();
    });
    themeList.appendChild(b);
  }
}

// ===== init =====
buildLangList();
buildThemeList();

setLang(getSavedLang());
setTheme(getSavedTheme());

// handlers (без падений)
if (langBtn) langBtn.addEventListener("click", openLang);
if (langClose) langClose.addEventListener("click", closeLang);
if (langOverlay) langOverlay.addEventListener("click", (e) => {
  if (e.target === langOverlay) closeLang();
});

if (themeBtn) themeBtn.addEventListener("click", openTheme);
if (themeClose) themeClose.addEventListener("click", closeTheme);
if (themeOverlay) themeOverlay.addEventListener("click", (e) => {
  if (e.target === themeOverlay) closeTheme();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { closeLang(); closeTheme(); }
});