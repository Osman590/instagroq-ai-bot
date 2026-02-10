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

/* ✅ ГЛАВНАЯ ЛОГИКА КНОПКИ "УДАЛИТЬ" */
function syncRemoveButton(){
  const mode = getMode();
  const modeId = mode?.id || "";
  const file = getFile();

  // txt2img — кнопки нет вообще
  if (modeId === "txt2img") {
    removeImgBtn.classList.add("hidden");
    return;
  }

  // остальные режимы — только если есть файл
  if (file) {
    removeImgBtn.classList.remove("hidden");
  } else {
    removeImgBtn.classList.add("hidden");
  }
}

function syncGenUIForMode(){
  const m = getMode();
  const modeId = m?.id || "";

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

function buildModes(){
  modeList.innerHTML = "";

  for (const m of getModes()) {
    const card = document.createElement("div");
    card.className = "modeCard";

    card.innerHTML = `
      <div class="modeImg">
        <div class="imgLoader" aria-hidden="true"></div>
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

    const markLoaded = () => imgWrap.classList.add("loaded");
    const markError = () => imgWrap.classList.add("error");

    img.addEventListener("load", markLoaded, { once: true });
    img.addEventListener("error", markError, { once: true });

    if (img.complete) {
      if (img.naturalWidth > 0) markLoaded();
      else markError();
    }

    card.onclick = () => {
      setMode(m.id);
      modeName.textContent = m.title;
      syncGenUIForMode();
      showGen();
    };

    modeList.appendChild(card);
  }
}

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
  setFile(null);
  previewWrap.classList.add("hidden");
  fileInput.value = "";
  syncRemoveButton();
};

changeModeBtn.onclick = () => {
  resetState();
  promptEl.value = "";
  setFile(null);
  previewWrap.classList.add("hidden");
  fileInput.value = "";
  loadingEl.classList.add("hidden");
  outEl.classList.add("hidden");
  if (resultImg) resultImg.removeAttribute("src");
  showPick();
};

genBtn.onclick = async () => {
  const m = getMode();
  const modeId = m?.id || "";
  if (!modeId) {
    alert("Сначала выбери функцию");
    return;
  }

  const prompt = (promptEl?.value || "").trim();
  const file = getFile();

  if (modeNeedsFile(modeId) && !file) {
    alert("Для этой функции нужно выбрать фото");
    return;
  }
  if (modeId === "txt2img" && !prompt) {
    alert("Напиши описание для генерации");
    return;
  }

  loadingEl.classList.remove("hidden");
  outEl.classList.add("hidden");
  genBtn.disabled = true;

  try {
    const res = await generateImage({ prompt, mode: modeId, file });
    const src = res?.image_base64 || res?.image_url || res?.url || "";
    if (!src) throw new Error("no_image");

    resultImg.src = src;
    loadingEl.classList.add("hidden");
    outEl.classList.remove("hidden");
  } catch {
    loadingEl.classList.add("hidden");
    outEl.classList.add("hidden");
    alert("Ошибка генерации");
  } finally {
    genBtn.disabled = false;
  }
};

buildModes();
showPick();