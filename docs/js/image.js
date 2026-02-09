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

// ===== gallery UI =====
const galleryBtn = document.getElementById("galleryBtn");
const fileInput = document.getElementById("fileInput");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

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
const promptEl = document.getElementById("prompt");
const chatZone = document.getElementById("chatZone");

function isInside(el, target){
  if (!el || !target) return false;
  return el === target || el.contains(target);
}

function hideKeyboard(){
  if (promptEl) promptEl.blur();
}

if (chatZone) {
  chatZone.addEventListener("pointerdown", (e) => {
    // если нажали не по textarea и не по кнопкам/превью — прячем клаву
    const t = e.target;

    const safe =
      isInside(promptEl, t) ||
      isInside(galleryBtn, t) ||
      isInside(removeImgBtn, t) ||
      isInside(fileInput, t) ||
      isInside(previewWrap, t);

    if (!safe) hideKeyboard();
  });
}

// ===== generate (пока заглушка) =====
const genBtn = document.getElementById("genBtn");
if (genBtn) {
  genBtn.addEventListener("click", () => {
    alert("Дальше подключим генерацию через Stability API.");
  });
}