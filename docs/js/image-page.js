// docs/js/image-page.js
import { getModes, setMode, getMode, setFile, getFile, resetState } from "./image.js";

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

    // ✅ loader -> показываем, пока конкретная картинка не загрузится
    const imgWrap = card.querySelector(".modeImg");
    const img = card.querySelector(".modeImg img");

    const markLoaded = () => {
      imgWrap.classList.add("loaded");
    };

    const markError = () => {
      imgWrap.classList.add("error");
    };

    img.addEventListener("load", markLoaded, { once: true });
    img.addEventListener("error", markError, { once: true });

    // если картинка уже в кэше
    if (img.complete) {
      if (img.naturalWidth > 0) markLoaded();
      else markError();
    }

    card.onclick = () => {
      setMode(m.id);
      modeName.textContent = m.title;
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
};

changeModeBtn.onclick = () => {
  resetState();
  showPick();
};

genBtn.onclick = () => {
  alert("Генерация будет подключена на следующем шаге");
};

buildModes();
showPick();