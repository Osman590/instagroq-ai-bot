// docs/js/image-page.js
import { getModes, setMode, getMode, setFile, getFile, resetState } from "./image.js";
import { generateImage } from "./image-api.js";

const tg = window.Telegram?.WebApp;

function applyVH(){
  document.documentElement.style.setProperty(
    "--vh",
    (tg?.viewportHeight || window.innerHeight) + "px"
  );
}

if (tg) {
  tg.ready();
  tg.expand();
  applyVH();
  tg.onEvent("viewportChanged", applyVH);
}

const screenPick = document.getElementById("screenPick");
const screenGen = document.getElementById("screenGen");
const modeList = document.getElementById("modeList");
const modeName = document.getElementById("modeName");

const fileInput = document.getElementById("fileInput");
const pickFileBtn = document.getElementById("pickFileBtn");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

const genBtn = document.getElementById("genBtn");
const changeModeBtn = document.getElementById("changeModeBtn");

const promptEl = document.getElementById("prompt");
const loadingEl = document.getElementById("loading");
const outEl = document.getElementById("out");
const resultImg = document.getElementById("resultImg");

/* =========================
   UI helpers
========================= */

function showPick(){
  screenPick.classList.add("active");
  screenGen.classList.remove("active");
}

function showGen(){
  screenPick.classList.remove("active");
  screenGen.classList.add("active");
}

function modeNeedsFile(modeId){
  return modeId !== "txt2img";
}

function syncRemoveButton(){
  const modeId = getMode()?.id || "";
  const file = getFile();

  if (modeId === "txt2img") {
    removeImgBtn.classList.add("hidden");
    return;
  }

  file ? removeImgBtn.classList.remove("hidden")
       : removeImgBtn.classList.add("hidden");
}

function syncGenUIForMode(){
  const modeId = getMode()?.id || "";
  const needFile = modeNeedsFile(modeId);

  pickFileBtn.style.display = needFile ? "" : "none";

  if (!needFile) {
    setFile(null);
    previewWrap.classList.add("hidden");
    fileInput.value = "";
  }

  loadingEl.classList.add("hidden");
  outEl.classList.add("hidden");
  if (resultImg) resultImg.removeAttribute("src");

  syncRemoveButton();
}

/* =========================
   BUILD MODES
========================= */

function buildModes(){
  modeList.innerHTML = "";

  for (const m of getModes()) {
    const card = document.createElement("div");
    card.className = "modeCard";

    card.innerHTML = `
      <div class="modeImg">
        <div class="imgLoader"></div>
        <img src="${m.image}" alt="">
      </div>
      <div class="modeBody">
        <div class="modeTitle">${m.title}</div>
        <div class="modeDesc">${m.desc}</div>
        <div class="modePrice">${m.price} ⭐</div>
      </div>
    `;

    const imgWrap = card.querySelector(".modeImg");
    const img = card.querySelector("img");

    img.onload = () => imgWrap.classList.add("loaded");
    img.onerror = () => imgWrap.classList.add("error");

    card.onclick = () => {
      setMode(m.id);
      modeName.textContent = m.title;
      syncGenUIForMode();
      showGen();
    };

    modeList.appendChild(card);
  }
}

/* =========================
   FILE HANDLING
========================= */

pickFileBtn.onclick = () => fileInput.click();

fileInput.onchange = () => {
  const file = fileInput.files[0];
  if (!file) return;

  setFile(file);
  previewImg.src = URL.createObjectURL(file);
  previewWrap.classList.remove("hidden");

  syncRemoveButton();
};

removeImgBtn.onclick = () => {
  // ✅ ПОЛНОСТЬЮ очищаем всё
  setFile(null);
  previewImg.removeAttribute("src");
  previewWrap.classList.add("hidden");
  fileInput.value = "";

  if (resultImg) resultImg.removeAttribute("src");
  outEl.classList.add("hidden");

  syncRemoveButton();
};

/* =========================
   CHANGE MODE
========================= */

changeModeBtn.onclick = () => {
  resetState();

  promptEl.value = "";
  setFile(null);
  previewImg.removeAttribute("src");
  previewWrap.classList.add("hidden");
  fileInput.value = "";

  loadingEl.classList.add("hidden");
  outEl.classList.add("hidden");
  if (resultImg) resultImg.removeAttribute("src");

  showPick();
};

/* =========================
   GENERATE
========================= */

genBtn.onclick = async () => {
  const modeId = getMode()?.id || "";
  const prompt = promptEl.value.trim();
  const file = getFile();

  if (!modeId) return alert("Сначала выбери функцию");
  if (modeNeedsFile(modeId) && !file) return alert("Выбери изображение");
  if (modeId === "txt2img" && !prompt) return alert("Напиши описание");

  loadingEl.classList.remove("hidden");
  outEl.classList.add("hidden");
  genBtn.disabled = true;

  try {
    const res = await generateImage({ prompt, mode: modeId, file });
    const src = res?.image_base64 || res?.image_url || "";

    if (!src) throw new Error();

    resultImg.src = src;
    loadingEl.classList.add("hidden");
    outEl.classList.remove("hidden");
  } catch {
    alert("Ошибка генерации");
    loadingEl.classList.add("hidden");
  } finally {
    genBtn.disabled = false;
  }
};

/* =========================
   KEYBOARD UX (ВАЖНО)
========================= */

/* ✅ закрывать клавиатуру при тапе вне input */
screenGen.addEventListener("click", (e) => {
  if (e.target !== promptEl) {
    promptEl.blur();
  }
});

/* ✅ при фокусе — прокрутить вверх */
promptEl.addEventListener("focus", () => {
  setTimeout(() => {
    promptEl.scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }, 300);
});

buildModes();
showPick();