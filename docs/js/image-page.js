import { fakeGenerate } from "./image-api.js";

const screens = {
  cards: document.getElementById("cardsScreen"),
  form: document.getElementById("formScreen"),
  loading: document.getElementById("loadingScreen"),
  result: document.getElementById("resultScreen"),
};

const galleryBtn = document.getElementById("galleryBtn");
const fileInput = document.getElementById("fileInput");
const generateBtn = document.getElementById("generateBtn");
const backBtn = document.getElementById("backBtn");
const closeResult = document.getElementById("closeResult");
const repeatBtn = document.getElementById("repeatBtn");
const resultImage = document.getElementById("resultImage");
const downloadBtn = document.getElementById("downloadBtn");

let currentMode = null;
let lastPayload = null;

function show(name){
  Object.values(screens).forEach(s=>s.classList.remove("active"));
  screens[name].classList.add("active");
}

document.querySelectorAll(".card").forEach(card=>{
  card.onclick = () => {
    currentMode = card.dataset.mode;
    galleryBtn.classList.toggle("hidden", currentMode === "text");
    show("form");
  };
});

backBtn.onclick = () => show("cards");

generateBtn.onclick = async () => {
  show("loading");
  lastPayload = {};
  const img = await fakeGenerate();
  resultImage.src = img;
  downloadBtn.href = img;
  show("result");
};

repeatBtn.onclick = generateBtn.onclick;

closeResult.onclick = () => show("form");