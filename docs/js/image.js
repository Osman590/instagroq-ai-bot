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

// ===== keep lang/theme on back (to index) =====
const url = new URL(window.location.href);
const lang = url.searchParams.get("lang") || (localStorage.getItem("miniapp_lang_v1") || "ru");
const theme = url.searchParams.get("theme") || (localStorage.getItem("miniapp_theme_v1") || "blue");

// ===== DOM =====
const backBtn = document.getElementById("backBtn");
const topTitle = document.getElementById("topTitle");

const modeView = document.getElementById("modeView");
const genView = document.getElementById("genView");
const modeList = document.getElementById("modeList");
const modeHint = document.getElementById("modeHint");

// генерация UI
const galleryBtn = document.getElementById("galleryBtn");
const fileInput = document.getElementById("fileInput");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");
const promptEl = document.getElementById("prompt");
const chatZone = document.getElementById("chatZone");
const genBtn = document.getElementById("genBtn");

// ===== back behavior =====
let currentMode = null;

function setBackToIndex(){
  if (!backBtn) return;
  backBtn.href = "./index.html?lang=" + encodeURIComponent(lang) + "&theme=" + encodeURIComponent(theme);
  backBtn.onclick = null; // обычная ссылка
}

function setBackToModes(){
  if (!backBtn) return;
  backBtn.href = "#";
  backBtn.onclick = (e) => {
    e.preventDefault();
    openModes();
  };
}

function openModes(){
  if (genView) genView.hidden = true;
  if (modeView) modeView.hidden = false;
  currentMode = null;

  if (topTitle) topTitle.textContent = "🎨 Генерация картинок";
  setBackToIndex();

  // на всякий случай прячем клаву
  if (promptEl) promptEl.blur();
}

function openGenerator(mode){
  currentMode = mode;

  if (modeView) modeView.hidden = true;
  if (genView) genView.hidden = false;

  if (topTitle) topTitle.textContent = mode?.title ? mode.title : "🎨 Генерация";
  if (modeHint && mode?.hint) modeHint.textContent = mode.hint;

  setBackToModes();

  // прокрутить вверх
  try { chatZone?.scrollTo({ top: 0, behavior: "smooth" }); } catch(e){}
}

// старт: по умолчанию показываем режимы
setBackToIndex();

// ===== MODELS (только UI-режимы, генерацию подключим позже) =====
const MODES = [
  {
    id: "txt2img",
    title: "🖌️ Нарисовать по тексту",
    desc: "Обычная генерация по промпту",
    hint: "Напиши промпт — получишь новую картинку.",
    badge: "от 2.5 кр."
  },
  {
    id: "img2img",
    title: "🧩 Редактировать картинку",
    desc: "Изменить стиль/детали по промпту",
    hint: "Выбери картинку из галереи + напиши что изменить.",
    badge: "от 2.5 кр."
  },
  {
    id: "remove_bg",
    title: "🪄 Удалить фон",
    desc: "Оставить объект, убрать фон",
    hint: "Выбери картинку из галереи — фон уберём.",
    badge: "5 кр."
  },
  {
    id: "search_recolor",
    title: "🎯 Поиск и перекраска",
    desc: "Найти объект и поменять цвет",
    hint: "Выбери картинку + напиши что и в какой цвет.",
    badge: "5 кр."
  },
  {
    id: "search_replace",
    title: "🔁 Поиск и замена",
    desc: "Заменить объект на другой",
    hint: "Выбери картинку + напиши что заменить и на что.",
    badge: "5 кр."
  },
  {
    id: "outpaint",
    title: "🧱 Расширить картинку",
    desc: "Дорисовать края (outpaint)",
    hint: "Выбери картинку + опиши что должно появиться по краям.",
    badge: "8 кр."
  },
];

function buildModeCards(){
  if (!modeList) return;
  modeList.innerHTML = "";

  for (const m of MODES){
    const card = document.createElement("button");
    card.type = "button";
    card.className = "modeCard";
    card.innerHTML = `
      <div class="modeCover" aria-hidden="true"></div>
      <div class="modeBody">
        <div class="modeTitle">${m.title}</div>
        <div class="modeDesc">${m.desc}</div>
        <div class="modeMeta">
          <span class="modeBadge">${m.badge || ""}</span>
          <span class="modeGo">Открыть →</span>
        </div>
      </div>
    `;
    card.addEventListener("click", () => openGenerator(m));
    modeList.appendChild(card);
  }
}

buildModeCards();
openModes();

// ===== gallery UI =====
let selectedFile = null;

function setPreview(file){
  selectedFile = file || null;

  if (!selectedFile) {
    if (previewWrap) previewWrap.hidden = true;
    if (previewImg) previewImg.src = "";
    return;
  }

  const blobUrl = URL.createObjectURL(selectedFile);
  if (previewImg) previewImg.src = blobUrl;
  if (previewWrap) previewWrap.hidden = false;
}

if (galleryBtn && fileInput) {
  galleryBtn.addEventListener("click", () => fileInput.click());
}

if (fileInput) {
  fileInput.addEventListener("change", () => {
    const f = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
    if (!f) return;
    setPreview(f);
  });
}

if (removeImgBtn && fileInput) {
  removeImgBtn.addEventListener("click", () => {
    fileInput.value = "";
    setPreview(null);
  });
}

// ===== hide keyboard when tap on “chat zone” =====
function isInside(el, target){
  if (!el || !target) return false;
  return el === target || el.contains(target);
}

function hideKeyboard(){
  if (promptEl) promptEl.blur();
}

function shouldKeepFocus(target){
  return (
    isInside(promptEl, target) ||
    isInside(galleryBtn, target) ||
    isInside(removeImgBtn, target) ||
    isInside(fileInput, target) ||
    isInside(previewWrap, target)
  );
}

if (chatZone) {
  // pointerdown
  chatZone.addEventListener("pointerdown", (e) => {
    if (!shouldKeepFocus(e.target)) hideKeyboard();
  });

  // iOS иногда лучше ловит touchstart
  chatZone.addEventListener("touchstart", (e) => {
    if (!shouldKeepFocus(e.target)) hideKeyboard();
  }, { passive:true });
}

// ===== generate (пока заглушка) =====
if (genBtn) {
  genBtn.addEventListener("click", () => {
    const modeName = currentMode?.id || "unknown";
    alert("Режим: " + modeName + "\nДальше подключим генерацию через Stability API.");
  });
}