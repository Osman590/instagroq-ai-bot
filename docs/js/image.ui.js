// docs/js/image.ui.js

// ===== modes (цены уже с твоей маржой) =====
const MODES = [
  {
    id: "txt2img",
    title: "🖌️ Нарисовать по тексту",
    sub: "Генерация по описанию (быстро и качественно).",
    desc: "Опиши результат: объект, стиль (аниме/реализм/3D), свет, детали, качество.",
    price: "4 cr.",
    model: "SD 3.5 Flash",
    needsImage: false,
    img: "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?auto=format&fit=crop&w=1400&q=80"
  },
  {
    id: "edit",
    title: "🧩 Редактировать картинку",
    sub: "Изменить стиль/детали на своей картинке по промпту.",
    desc: "Загрузи картинку и напиши, что изменить: фон, детали, объекты, стиль.",
    price: "8 cr.",
    model: "SD 3.5 (Image Edit)",
    needsImage: true,
    img: "https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=1400&q=80"
  },
  {
    id: "style",
    title: "✨ Перенос стиля",
    sub: "Сделать картинку в выбранном стиле (сильный визуальный эффект).",
    desc: "Загрузи картинку и напиши стиль: «аниме», «киберпанк», «масло», «3D», и т.д.",
    price: "12 cr.",
    model: "Style Transfer",
    needsImage: true,
    img: "https://images.unsplash.com/photo-1526318472351-c75fcf070305?auto=format&fit=crop&w=1400&q=80"
  }
];

let currentMode = MODES[0];
let selectedFile = null;

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
const placeholder= document.getElementById("placeholder");
const outImg     = document.getElementById("outImg");

const loading    = document.getElementById("loading");
const bottomRow  = document.getElementById("bottomRow");
const againBtn   = document.getElementById("againBtn");

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

  if (modeTitle) modeTitle.textContent = m.title.replace(/^[^ ]+ /, "");
  if (modeDesc)  modeDesc.textContent  = m.desc;
  if (modePrice) modePrice.textContent = m.price;
  if (modeModel) modeModel.textContent = m.model;

  // если режим не требует картинку — убираем галерею/превью и центрируем кнопку
  if (m.needsImage) {
    if (galleryBtn) galleryBtn.hidden = false;
    if (btnRow) btnRow.classList.remove("centerOnly");
  } else {
    if (galleryBtn) galleryBtn.hidden = true;
    if (btnRow) btnRow.classList.add("centerOnly");
    if (fileInput) fileInput.value = "";
    setPreview(null);
  }

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

  // во время загрузки — прячем ввод (кнопки/поле)
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

  if (currentMode.needsImage && !selectedFile) {
    alert("Сначала выбери картинку в Галерее.");
    return;
  }

  if (!prompt) {
    alert("Напиши промпт.");
    return;
  }

  setLoading(true);

  const seed = encodeURIComponent(currentMode.id + "-" + prompt.slice(0, 40));
  const demoUrl = "https://picsum.photos/seed/" + seed + "/1024/768";

  setTimeout(() => {
    showResultImage(demoUrl);
  }, 1400);
}

if (genBtn) {
  genBtn.addEventListener("click", fakeGenerate);
}

// ===== init =====
export function initImageUI(){
  buildModeCards();
  applyMode(MODES[0]);
  showScreen("pick");
}