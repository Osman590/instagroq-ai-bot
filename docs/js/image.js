// docs/js/image.js
const tg = window.Telegram?.WebApp || null;

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

// ===== keep lang/theme on back =====
const url = new URL(window.location.href);
const lang = url.searchParams.get("lang") || (localStorage.getItem("miniapp_lang_v1") || "ru");
const theme = url.searchParams.get("theme") || (localStorage.getItem("miniapp_theme_v1") || "blue");

const backBtn = document.getElementById("backBtn");
if (backBtn) {
  backBtn.href = "./index.html?lang=" + encodeURIComponent(lang) + "&theme=" + encodeURIComponent(theme);
}

// ===== smooth exit on back =====
function smoothGo(href){
  document.body.classList.remove("pageIn");
  document.body.classList.add("pageOut");
  setTimeout(() => { window.location.href = href; }, 260);
}
if (backBtn) {
  backBtn.addEventListener("click", (e) => {
    e.preventDefault();
    smoothGo(backBtn.href);
  });
}

// ===== MODE CONFIG (цены в ⭐️) =====
// базовая себестоимость "Flash" ~ 2.5 credits → с маржой/комиссиями округляем до 4 ⭐️
const MODES = [
  {
    id: "txt2img",
    title: "Нарисовать по тексту",
    desc: "Создать изображение по описанию: стиль, свет, композиция, детали.",
    price: 4,
    needsImage: false,
    cover: "https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=1200&q=85"
  },
  {
    id: "edit",
    title: "Редактировать картинку",
    desc: "Поменять детали/стиль по твоему описанию. Нужна картинка из галереи.",
    price: 8,
    needsImage: true,
    cover: "https://images.unsplash.com/photo-1541961017774-22349e4a1262?auto=format&fit=crop&w=1200&q=85"
  },
  {
    id: "style",
    title: "Перенос стиля",
    desc: "Сделать изображение в стиле: аниме, 3D, масло, киберпанк и т.д. Нужна картинка.",
    price: 12,
    needsImage: true,
    cover: "https://images.unsplash.com/photo-1535909339361-9b4f7f33a3b9?auto=format&fit=crop&w=1200&q=85"
  },
  {
    id: "bg_remove",
    title: "Удалить фон",
    desc: "Убрать фон и оставить объект. Отлично для товаров/аватарок. Нужна картинка.",
    price: 6,
    needsImage: true,
    cover: "https://images.unsplash.com/photo-1526318472351-c75fcf070305?auto=format&fit=crop&w=1200&q=85"
  },
  {
    id: "upscale",
    title: "Улучшить качество (4K)",
    desc: "Повысить резкость и разрешение изображения. Нужна картинка.",
    price: 14,
    needsImage: true,
    cover: "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&q=85"
  }
];

const STORAGE_MODE = "miniapp_img_mode_v1";

// ===== DOM =====
const modeScreen = document.getElementById("modeScreen");
const genScreen  = document.getElementById("genScreen");
const modeList   = document.getElementById("modeList");

const selectedModeChip  = document.getElementById("selectedModeChip");
const selectedModePrice = document.getElementById("selectedModePrice");
const genDesc = document.getElementById("genDesc");
const changeModeBtn = document.getElementById("changeModeBtn");

const actionsRow = document.getElementById("actionsRow");
const galleryBtn = document.getElementById("galleryBtn");
const genBtn     = document.getElementById("genBtn");

const fileInput   = document.getElementById("fileInput");
const previewWrap = document.getElementById("previewWrap");
const previewImg  = document.getElementById("previewImg");
const removeImgBtn= document.getElementById("removeImgBtn");

const promptBox = document.getElementById("promptBox");
const promptEl  = document.getElementById("prompt");
const chatZone  = document.getElementById("chatZone");

const loadingBox = document.getElementById("loadingBox");
const result2    = document.getElementById("result2");
const outImg     = document.getElementById("outImg");
const regenBtn   = document.getElementById("regenBtn");

// ===== state =====
let selectedFile = null;
let currentModeId = null;

function getSavedMode(){
  try { return localStorage.getItem(STORAGE_MODE) || "txt2img"; }
  catch(e){ return "txt2img"; }
}
function saveMode(id){
  try { localStorage.setItem(STORAGE_MODE, id); } catch(e){}
}
function getModeById(id){
  return MODES.find(m => m.id === id) || MODES[0];
}

// ===== UI NAV =====
function showModeList(){
  if (modeScreen) modeScreen.hidden = false;
  if (genScreen) genScreen.hidden = true;
  if (chatZone) chatZone.scrollTo({ top: 0, behavior: "smooth" });
}
function showGen(){
  if (modeScreen) modeScreen.hidden = true;
  if (genScreen) genScreen.hidden = false;
  if (chatZone) chatZone.scrollTo({ top: 0, behavior: "smooth" });
}

function setCurrentMode(id){
  currentModeId = id;
  const m = getModeById(id);

  if (selectedModeChip) selectedModeChip.textContent = m.title;
  if (selectedModePrice) selectedModePrice.textContent = `${m.price} ⭐️`;
  if (genDesc) genDesc.textContent = m.desc;

  // если режим не требует картинку — скрываем галерею/превью полностью
  if (m.needsImage) {
    if (galleryBtn) galleryBtn.hidden = false;
    if (actionsRow) actionsRow.classList.remove("centerOnly");
  } else {
    if (galleryBtn) galleryBtn.hidden = true;
    if (actionsRow) actionsRow.classList.add("centerOnly");
    if (fileInput) fileInput.value = "";
    setPreview(null);
  }

  saveMode(id);
  resetToInputState();
}

// ===== build cards =====
function buildModeCards(){
  if (!modeList) return;
  modeList.innerHTML = "";

  for (const m of MODES){
    const card = document.createElement("button");
    card.type = "button";
    card.className = "modeCard";

    card.innerHTML = `
      <div class="modeCover" style="background-image:url('${m.cover}')">
        <div class="modeOverlay"></div>
        <div class="modePrice">от ${m.price} ⭐️</div>
      </div>
      <div class="modeBody">
        <div class="modeTitleRow">
          <div class="modeTitleText">${m.title}</div>
          <div class="modeOpen">Открыть →</div>
        </div>
        <div class="modeDesc">${m.desc}</div>
      </div>
    `;

    card.addEventListener("click", () => {
      setCurrentMode(m.id);
      showGen();
    });

    modeList.appendChild(card);
  }
}

// ===== gallery preview =====
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

// ===== hide keyboard when tap on zone =====
function isInside(el, target){
  if (!el || !target) return false;
  return el === target || el.contains(target);
}
function hideKeyboard(){
  if (promptEl) promptEl.blur();
}
if (chatZone) {
  chatZone.addEventListener("pointerdown", (e) => {
    const t = e.target;
    const safe =
      isInside(promptEl, t) ||
      isInside(actionsRow, t) ||
      isInside(previewWrap, t) ||
      isInside(changeModeBtn, t) ||
      isInside(regenBtn, t);
    if (!safe) hideKeyboard();
  });
}

// ===== states =====
function resetToInputState(){
  if (actionsRow) actionsRow.hidden = false;
  if (promptBox) promptBox.hidden = false;

  if (loadingBox) loadingBox.hidden = true;
  if (result2) result2.hidden = true;
  if (regenBtn) regenBtn.hidden = true;

  if (outImg) outImg.src = "";
}
function showLoadingState(){
  hideKeyboard();

  if (actionsRow) actionsRow.hidden = true;
  if (promptBox) promptBox.hidden = true;

  if (result2) result2.hidden = true;
  if (regenBtn) regenBtn.hidden = true;

  if (loadingBox) loadingBox.hidden = false;
}
function showResultState(imgUrl){
  if (loadingBox) loadingBox.hidden = true;

  if (actionsRow) actionsRow.hidden = true;
  if (promptBox) promptBox.hidden = true;

  if (outImg) outImg.src = imgUrl;
  if (result2) result2.hidden = false;
  if (regenBtn) regenBtn.hidden = false;
}

// ===== fake generate (демо) =====
function fakeGenerate(){
  const demo = "https://images.unsplash.com/photo-1520975682042-09028f65f53a?auto=format&fit=crop&w=1200&q=85";
  showLoadingState();
  setTimeout(() => showResultState(demo), 1400);
}

if (genBtn) {
  genBtn.addEventListener("click", () => {
    const m = getModeById(currentModeId || "txt2img");
    const prompt = (promptEl?.value || "").trim();

    if (m.needsImage && !selectedFile) {
      tg?.showToast?.("Нужна картинка из галереи");
      if (!tg?.showToast) alert("Нужна картинка из галереи");
      return;
    }
    if (!prompt && !selectedFile) {
      tg?.showToast?.("Напиши промпт");
      if (!tg?.showToast) alert("Напиши промпт");
      return;
    }

    fakeGenerate();
  });
}

if (regenBtn) {
  regenBtn.addEventListener("click", () => {
    resetToInputState();
  });
}

if (changeModeBtn) {
  changeModeBtn.addEventListener("click", () => {
    showModeList();
  });
}

// ===== init =====
buildModeCards();

const qpMode = url.searchParams.get("mode");
const initialMode = (qpMode && MODES.some(m => m.id === qpMode)) ? qpMode : getSavedMode();
setCurrentMode(initialMode);

if (qpMode && MODES.some(m => m.id === qpMode)) showGen();
else showModeList();