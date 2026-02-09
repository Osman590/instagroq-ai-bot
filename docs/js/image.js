// docs/js/image.js
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

// ===== MODE CONFIG =====
// себестоимость: SD 3.5 Flash = 2.5 credits
// твоя прибыль 32% => 2.5 / 0.68 = 3.68 => округляем до 4 cr
const PRICE_TXT2IMG = 4;
const PRICE_EDIT = 8;   // редактирование дороже (больше операций)
const PRICE_STYLE = 12; // перенос стиля дороже

const MODES = [
  {
    id: "txt2img",
    title: "Нарисовать по тексту",
    desc: "Обычная генерация по промпту",
    price: PRICE_TXT2IMG,
    cover: "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80"
  },
  {
    id: "edit",
    title: "Редактировать картинку",
    desc: "Изменить детали/стиль по промпту",
    price: PRICE_EDIT,
    cover: "https://images.unsplash.com/photo-1541961017774-22349e4a1262?auto=format&fit=crop&w=1200&q=80"
  },
  {
    id: "style",
    title: "Перенос стиля",
    desc: "Сделать в выбранном стиле (аниме/арт/кино)",
    price: PRICE_STYLE,
    cover: "https://images.unsplash.com/photo-1526481280695-3c687fd643ed?auto=format&fit=crop&w=1200&q=80"
  }
];

const STORAGE_MODE = "miniapp_img_mode_v1";

// ===== DOM =====
const modeScreen = document.getElementById("modeScreen");
const genScreen = document.getElementById("genScreen");
const modeList = document.getElementById("modeList");

const selectedModeChip = document.getElementById("selectedModeChip");
const selectedModePrice = document.getElementById("selectedModePrice");
const changeModeBtn = document.getElementById("changeModeBtn");

const galleryBtn = document.getElementById("galleryBtn");
const fileInput = document.getElementById("fileInput");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

const promptEl = document.getElementById("prompt");
const chatZone = document.getElementById("chatZone");

const actionsRow = document.getElementById("actionsRow");
const promptBox = document.getElementById("promptBox");

const loadingBox = document.getElementById("loadingBox");
const result2 = document.getElementById("result2");
const outImg = document.getElementById("outImg");

const genBtn = document.getElementById("genBtn");
const regenBtn = document.getElementById("regenBtn");

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
}

function showGen(){
  if (modeScreen) modeScreen.hidden = true;
  if (genScreen) genScreen.hidden = false;
}

function setCurrentMode(id){
  currentModeId = id;
  const m = getModeById(id);
  if (selectedModeChip) selectedModeChip.textContent = m.title;
  if (selectedModePrice) selectedModePrice.textContent = `${m.price} cr.`;
  saveMode(id);
}

// ===== build cards =====
function buildModeCards(){
  if (!modeList) return;
  modeList.innerHTML = "";

  for (const m of MODES){
    const card = document.createElement("button");
    card.type = "button";
    card.className = "modeCard";
    card.setAttribute("data-mode", m.id);

    card.innerHTML = `
      <div class="modeCover" style="background-image:url('${m.cover}')">
        <div class="modeOverlay"></div>
        <div class="modePrice">от ${m.price} cr.</div>
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

      // плавный переход внутри страницы
      document.body.classList.add("fadeSwap");
      setTimeout(() => {
        document.body.classList.remove("fadeSwap");
        showGen();
        resetToInputState();
      }, 220);
    });

    modeList.appendChild(card);
  }
}

// ===== gallery UI =====
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

if (chatZone) {
  chatZone.addEventListener("pointerdown", (e) => {
    const t = e.target;

    const safe =
      isInside(promptEl, t) ||
      isInside(galleryBtn, t) ||
      isInside(removeImgBtn, t) ||
      isInside(fileInput, t) ||
      isInside(previewWrap, t) ||
      isInside(changeModeBtn, t);

    if (!safe) hideKeyboard();
  });
}

// ===== Generation states =====
function resetToInputState(){
  // show input + actions
  if (actionsRow) actionsRow.hidden = false;
  if (promptBox) promptBox.hidden = false;

  // hide loading/result
  if (loadingBox) loadingBox.hidden = true;
  if (result2) result2.hidden = true;
  if (regenBtn) regenBtn.hidden = true;

  // clear result image
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

// ===== Generate (пока имитация) =====
function fakeGenerate(){
  // чтобы выглядело реально — задержка + картинка
  const demo = "https://images.unsplash.com/photo-1520975682042-09028f65f53a?auto=format&fit=crop&w=1200&q=80";
  showLoadingState();
  setTimeout(() => showResultState(demo), 1400);
}

if (genBtn) {
  genBtn.addEventListener("click", () => {
    const prompt = (promptEl?.value || "").trim();
    // можно разрешить без текста, но лучше так:
    if (!prompt && !selectedFile) {
      tg?.showToast?.("Напиши промпт или выбери картинку");
      if (!tg?.showToast) alert("Напиши промпт или выбери картинку");
      return;
    }
    fakeGenerate();
  });
}

if (regenBtn) {
  regenBtn.addEventListener("click", () => {
    resetToInputState();
    // не очищаем промпт/превью — пользователь может поправить
  });
}

if (changeModeBtn) {
  changeModeBtn.addEventListener("click", () => {
    document.body.classList.add("fadeSwap");
    setTimeout(() => {
      document.body.classList.remove("fadeSwap");
      showModeList();
    }, 220);
  });
}

// ===== init =====
buildModeCards();
setCurrentMode(getSavedMode());

// если открыли по прямой ссылке с ?mode=... можно сразу в генерацию
const qpMode = url.searchParams.get("mode");
if (qpMode && MODES.some(m => m.id === qpMode)) {
  setCurrentMode(qpMode);
  showGen();
} else {
  showModeList();
}
resetToInputState();