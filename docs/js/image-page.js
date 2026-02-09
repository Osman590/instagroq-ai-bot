// docs/js/image-page.js

import { getModes, setMode, getMode, setFile, getFile, resetState } from "./image.js";

// ===== Telegram / VH =====
const tg = window.Telegram?.WebApp;

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

// ===== DOM =====
const screenPick = document.getElementById("screenPick");
const screenGen  = document.getElementById("screenGen");

const modeList = document.getElementById("modeList");
const modeName = document.getElementById("modeName");
const changeModeBtn = document.getElementById("changeModeBtn");

const fileInput = document.getElementById("fileInput");
const pickFileBtn = document.getElementById("pickFileBtn");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const removeImgBtn = document.getElementById("removeImgBtn");

const genBtn = document.getElementById("genBtn");
const loading = document.getElementById("loading");
const out = document.getElementById("out");

// ===== helpers =====
function showPick(){
  screenPick.classList.add("active");
  screenGen.classList.remove("active");
}

function showGen(){
  screenPick.classList.remove("active");
  screenGen.classList.add("active");
}

function buildModes(){
  modeList.innerHTML = "";
  const modes = getModes();

  for (const m of modes){
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="info">
        <div class="title">${m.title}</div>
        <div class="desc">${m.desc}</div>
      </div>
    `;
    card.addEventListener("click", () => {
      setMode(m.id);
      modeName.textContent = m.title;
      showGen();
    });
    modeList.appendChild(card);
  }
}

function updatePreview(){
  const file = getFile();
  if (!file){
    previewWrap.classList.add("hidden");
    previewImg.src = "";
    return;
  }
  const url = URL.createObjectURL(file);
  previewImg.src = url;
  previewWrap.classList.remove("hidden");
}

// ===== events =====
changeModeBtn.addEventListener("click", () => {
  resetState();
  showPick();
});

pickFileBtn.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  const f = fileInput.files?.[0];
  if (!f) return;
  setFile(f);
  updatePreview();
});

removeImgBtn.addEventListener("click", () => {
  setFile(null);
  fileInput.value = "";
  updatePreview();
});

genBtn.addEventListener("click", () => {
  // пока заглушка
  loading.classList.remove("hidden");
  out.classList.add("hidden");

  setTimeout(() => {
    loading.classList.add("hidden");
    out.classList.remove("hidden");
  }, 1200);
});

// ===== init =====
buildModes();
showPick();