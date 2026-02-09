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

// ===== DOM =====
const screenPick = document.getElementById("screenPick");
const screenGen  = document.getElementById("screenGen");
const modeList   = document.getElementById("modeList");

const modeTitle  = document.getElementById("modeTitle");
const modeDesc   = document.getElementById("modeDesc");
const modePrice  = document.getElementById("modePrice");
const modeModel  = document.getElementById("modeModel");
const changeModeBtn = document.getElementById("changeModeBtn");

const galleryBtn = document.getElementById("galleryBtn");
const genBtn     = document.getElementById("genBtn");
const btnRow     = document.getElementById("btnRow");

const fileInput  = document.getElementById("fileInput");
const previewWrap= document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

const promptEl   = document.getElementById("prompt");
const chatZone   = document.getElementById("chatZone");

const inputBlock = document.getElementById("inputBlock");
const resultBox  = document.getElementById("result");
const placeholder= document.getElementById("placeholder");
const outImg     = document.getElementById("outImg");

const loading    = document.getElementById("loading");
const bottomRow  = document.getElementById("bottomRow");
const againBtn   = document.getElementById("againBtn");

// ===== modes (цены уже с твоей маржой) =====
// Примечание: "SD 3.5 Flash" как самый дешёвый/адекватный по качеству (2.5 cr. базово),
// а цены в UI выставлены так, чтобы оставалась прибыль и покрывались комиссии.
const MODES = [
  {
    id: "txt2img",
    title: "🖌️ Нарисовать по тексту",
    sub: "Обычная генерация по описанию (быстро и недорого).",
    desc: "Напиши промпт: что нарисовать, стиль, детали, свет, качество.",
    price: "4 cr.",
    model: "SD 3.5 Flash",
    needsImage: false,
    img: "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=70"
  },
  {
    id: "edit",
    title: "🧩 Редактировать картинку",
    sub: "Поменять стиль/детали на своей картинке по промпту.",
    desc: "Загрузи картинку из галереи и напиши, что изменить (стиль, детали, фон, объекты).",
    price: "8 cr.",
    model: "SD 3.5 (Image Edit)",
    needsImage: true,
    img: "https://images.unsplash.com/photo-1541963463532-d68292c34b19?auto=format&fit=crop&w=1200&q=70"
  },
  {
    id: "style",
    title: "✨ Перенос стиля",
    sub: "Сделать картинку в нужном визуальном стиле (выраженный эффект).",
    desc: "Загрузи картинку и напиши стиль: «аниме», «киберпанк», «масло», «3d», и т.д.",
    price: "12 cr.",
    model: "Style Transfer",
    needsImage: true,
    img: "https://images.unsplash.com/photo-1496307653780-42ee777d4833?auto=format&fit=crop&w=1200&q=70"
  }
];

let currentMode = MODES[0];
let selectedFile = null;

// ===== helpers =====
function isInside(el, target){
  if (!el || !target) return false;
  return el === target || el.contains(target);
}

function hideKeyboard(){
  if (promptEl) promptEl.blur();
}

// скрыть клавиатуру при тапе по зоне (вне textarea/кнопок/превью)
if (chatZone) {
  chatZone.addEventListener("pointerdown", (e) => {
    const t = e.target;

    const safe =
      isInside(promptEl, t) ||
      isInside(galleryBtn, t) ||
      isInside(genBtn, t) ||
      isInside(removeImgBtn, t) ||
      isInside(fileInput, t) ||
      isInside(previewWrap, t) ||
      isInside(modeList, t) ||
      isInside(changeModeBtn, t) ||
      isInside(againBtn, t);

    if (!safe) hideKeyboard();
  });
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

// ===== UI: screens =====
function showScreen(which){
  const isPick = which === "pick";

  if (screenPick) {
    screenPick.classList.toggle("screenActive", isPick);
    screenPick.classList.toggle("screenLeave", !isPick);
    screenPick.setAttribute("aria-hidden", String(!isPick));
  }
  if (screenGen) {
    screenGen.classList.toggle("screenActive", !isPick);
    screenGen.classList.toggle("screenLeave", isPick);
    screenGen.setAttribute("aria-hidden", String(isPick));
  }

  // мягкая прокрутка в начало при переключении
  if (chatZone) chatZone.scrollTo({ top: 0, behavior: "smooth" });
}

function applyMode(m){
  currentMode = m;

  if (modeTitle) modeTitle.textContent = m.title.replace(/^[^ ]+ /, ""); // без эмодзи в заголовке
  if (modeDesc)  modeDesc.textContent  = m.desc;
  if (modePrice) modePrice.textContent = m.price;
  if (modeModel) modeModel.textContent = m.model;

  // если режим не требует картинку — убираем галерею/превью
  if (m.needsImage) {
    if (galleryBtn) galleryBtn.hidden = false;
    if (btnRow) btnRow.classList.remove("centerOnly");
  } else {
    if (galleryBtn) galleryBtn.hidden = true;
    if (btnRow) btnRow.classList.add("centerOnly");
    // сброс выбранной картинки
    if (fileInput) fileInput.value = "";
    setPreview(null);
  }

  // сброс результата при смене режима
  resetToInput();
}

function buildModeCards(){
  if (!modeList) return;
  modeList.innerHTML = "";

  for (const m of MODES) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "modeCard";
    card.setAttribute("role", "listitem");

    card.innerHTML = `
      <div class="modeMedia" style="background-image:url('${m.img}')">
        <div class="modeOverlay"></div>
        <div class="modePrice">${m.price}</div>
      </div>
      <div class="modeBody">
        <div class="modeTitle">${m.title}</div>
        <div class="modeSub">${m.sub}</div>
        <div class="modeOpen">Открыть →</div>
      </div>
    `;

    card.addEventListener("click", () => {
      applyMode(m);
      showScreen("gen");
    });

    modeList.appendChild(card);
  }
}

if (changeModeBtn) {
  changeModeBtn.addEventListener("click", () => showScreen("pick"));
}

// ===== generation states =====
function setLoading(on){
  if (loading) loading.hidden = !on;

  // во время загрузки — прячем ввод и показываем только loader в result
  if (inputBlock) inputBlock.hidden = on;
  if (bottomRow) bottomRow.hidden = true;

  // placeholder / output
  if (placeholder) placeholder.hidden = on;
  if (outImg) outImg.hidden = true;
}

function showResultImage(src){
  if (!src) return;

  if (loading) loading.hidden = true;
  if (placeholder) placeholder.hidden = true;

  if (outImg) {
    outImg.src = src;
    outImg.hidden = false;
  }

  if (bottomRow) bottomRow.hidden = false;
  if (inputBlock) inputBlock.hidden = true;
}

function resetToInput(){
  if (loading) loading.hidden = true;
  if (placeholder) {
    placeholder.textContent = "Здесь появится результат";
    placeholder.hidden = false;
  }
  if (outImg) {
    outImg.hidden = true;
    outImg.src = "";
  }

  if (inputBlock) inputBlock.hidden = false;
  if (bottomRow) bottomRow.hidden = true;
}

if (againBtn) {
  againBtn.addEventListener("click", () => {
    resetToInput();
    if (promptEl) promptEl.focus();
  });
}

// ===== generate (пока демо, без API) =====
function fakeGenerate(){
  const prompt = (promptEl?.value || "").trim();

  // если режим требует картинку — она должна быть выбрана
  if (currentMode.needsImage && !selectedFile) {
    alert("Сначала выбери картинку в Галерее.");
    return;
  }

  if (!prompt) {
    alert("Напиши промпт.");
    return;
  }

  setLoading(true);

  // демо-результат: картинка по seed (чтобы каждый раз было похоже, но разное)
  const seed = encodeURIComponent(currentMode.id + "-" + prompt.slice(0, 40));
  const demoUrl = "https://picsum.photos/seed/" + seed + "/1024/768";

  // имитация ожидания
  setTimeout(() => {
    showResultImage(demoUrl);
  }, 1400);
}

if (genBtn) {
  genBtn.addEventListener("click", fakeGenerate);
}

// ===== init =====
buildModeCards();
applyMode(MODES[0]);
showScreen("pick");