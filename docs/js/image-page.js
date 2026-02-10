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
  // txt2img — без фото, всё остальное требует входную картинку
  return modeId !== "txt2img";
}

function syncGenUIForMode(){
  const m = getMode();
  const modeId = m?.id || "";

  // показать/скрыть выбор фото по режиму
  const needFile = modeNeedsFile(modeId);
  pickFileBtn.style.display = needFile ? "" : "none";
  if (!needFile) {
    // если режим без фото — сбрасываем выбранный файл и превью
    setFile(null);
    previewWrap.classList.add("hidden");
    fileInput.value = "";
  }

  // сброс результата при переключении режима
  loadingEl.classList.add("hidden");
  outEl.classList.add("hidden");
  if (resultImg) resultImg.removeAttribute("src");
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
    const img = card.querySelector(".modeImg img");

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
};

removeImgBtn.onclick = () => {
  setFile(null);
  previewWrap.classList.add("hidden");
  fileInput.value = "";
};

changeModeBtn.onclick = () => {
  resetState();
  // сброс UI
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

  // проверки по режимам
  if (modeNeedsFile(modeId) && !file) {
    alert("Для этой функции нужно выбрать фото");
    return;
  }
  if (modeId === "txt2img" && !prompt) {
    alert("Напиши описание для генерации");
    return;
  }

  // UI состояние
  loadingEl.classList.remove("hidden");
  outEl.classList.add("hidden");
  genBtn.disabled = true;

  try {
    const res = await generateImage({ prompt, mode: modeId, file });

    // ожидаем один из вариантов:
    // { image_url: "https://..." }  или  { image_base64: "data:image/png;base64,..." }
    const url = res?.image_url || res?.url || "";
    const b64 = res?.image_base64 || res?.base64 || "";

    const src = b64 || url;
    if (!src) {
      throw new Error("no_image_in_response");
    }

    resultImg.src = src;
    loadingEl.classList.add("hidden");
    outEl.classList.remove("hidden");
  } catch (e) {
    loadingEl.classList.add("hidden");
    outEl.classList.add("hidden");
    alert("Ошибка генерации");
  } finally {
    genBtn.disabled = false;
  }
};

buildModes();
showPick();