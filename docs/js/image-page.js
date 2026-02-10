import { getModes, setMode, getMode, setFile, getFile, resetState } from "./image.js";
import { generateImage } from "./image-api.js";

const tg = window.Telegram?.WebApp;

// ===== vh =====
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

// ===== elements =====
const screenPick = document.getElementById("screenPick");
const screenGen  = document.getElementById("screenGen");
const modeList  = document.getElementById("modeList");
const modeName  = document.getElementById("modeName");

const fileInput    = document.getElementById("fileInput");
const pickFileBtn  = document.getElementById("pickFileBtn");
const previewWrap  = document.getElementById("previewWrap");
const previewImg   = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

const promptEl  = document.getElementById("prompt");
const genBtn    = document.getElementById("genBtn");
const changeModeBtn = document.getElementById("changeModeBtn");

const loadingEl = document.getElementById("loading");
const outEl     = document.getElementById("out");
const resultImg = document.getElementById("resultImg");
const genStage  = document.getElementById("genStage");

// ===== helpers =====
const showPick = () => {
  screenPick.classList.add("active");
  screenGen.classList.remove("active");
};

const showGen = () => {
  screenPick.classList.remove("active");
  screenGen.classList.add("active");
};

const modeNeedsFile = (id) => id !== "txt2img";

const hide = (el) => {
  if (!el) return;
  el.classList.add("hidden");
  el.style.display = "none";
};

const show = (el) => {
  if (!el) return;
  el.classList.remove("hidden");
  el.style.display = "";
};

const syncRemoveBtn = () => {
  const m = getMode()?.id;
  const file = getFile();
  if (m === "txt2img" || !file) hide(removeImgBtn);
  else show(removeImgBtn);
};

const resetResult = () => {
  if (resultImg) resultImg.removeAttribute("src");
  hide(outEl);
};

const setGeneratingUI = (on) => {
  if (on) {
    hide(promptEl);
    hide(genBtn);
    hide(changeModeBtn);
    hide(pickFileBtn);
    hide(previewWrap);
    hide(removeImgBtn);

    genStage.classList.add("is-loading");
    genStage.classList.remove("is-result");

    show(loadingEl);
    hide(outEl);
  } else {
    hide(loadingEl);
  }
};

// ===== modes =====
function buildModes(){
  modeList.innerHTML = "";

  for (const m of getModes()) {
    const card = document.createElement("div");
    card.className = "modeCard";
    card.innerHTML = `
      <div class="modeImg">
        <div class="imgLoader"></div>
        <img src="${m.image}">
      </div>
      <div class="modeBody">
        <div class="modeTitle">${m.title}</div>
        <div class="modeDesc">${m.desc}</div>
        <div class="modePrice">${m.price} ⭐</div>
      </div>
    `;

    const img = card.querySelector("img");
    const wrap = card.querySelector(".modeImg");

    img.onload  = () => wrap.classList.add("loaded");
    img.onerror = () => wrap.classList.add("error");

    card.onclick = () => {
      setMode(m.id);
      modeName.textContent = m.title;
      resetResult();
      syncRemoveBtn();
      showGen();
    };

    modeList.appendChild(card);
  }
}

// ===== file =====
pickFileBtn.onclick = () => fileInput.click();

fileInput.onchange = () => {
  const f = fileInput.files[0];
  if (!f) return;
  setFile(f);
  previewImg.src = URL.createObjectURL(f);
  show(previewWrap);
  syncRemoveBtn();
};

removeImgBtn.onclick = () => {
  setFile(null);
  previewImg.removeAttribute("src");
  fileInput.value = "";
  hide(previewWrap);
  hide(removeImgBtn);
};

// ===== keyboard UX =====
screenGen.addEventListener("pointerdown", (e) => {
  if (e.target !== promptEl) promptEl?.blur();
});

promptEl?.addEventListener("focus", () => {
  setTimeout(() => {
    promptEl.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 300);
});

// ===== generate =====
genBtn.onclick = async () => {
  const modeId = getMode()?.id;
  const prompt = promptEl.value.trim();
  const file   = getFile();

  if (!modeId) return alert("Выбери функцию");
  if (modeNeedsFile(modeId) && !file) return alert("Нужно фото");
  if (modeId === "txt2img" && !prompt) return alert("Напиши описание");

  promptEl.blur();
  setGeneratingUI(true);

  let seconds = 20;
  const eta = loadingEl.querySelector(".genEta");
  if (eta) eta.textContent = seconds;

  const timer = setInterval(() => {
    seconds = Math.max(0, seconds - 1);
    if (eta) eta.textContent = seconds;
    if (!seconds) clearInterval(timer);
  }, 1000);

  try {
    const res = await generateImage({ prompt, mode: modeId, file });
    clearInterval(timer);

    const src = res.image_base64 || res.image_url;
    if (!src) throw 1;

    hide(loadingEl);
    resultImg.src = src;
    show(outEl);

    genStage.classList.remove("is-loading");
    genStage.classList.add("is-result");

  } catch {
    clearInterval(timer);
    alert("Ошибка генерации");
    setGeneratingUI(false);
  }
};

// ===== init =====
buildModes();
showPick();