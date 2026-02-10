// docs/js/image-page.js - УПРОЩЕННАЯ ВЕРСИЯ ДЛЯ ТЕСТА
console.log("🚀 image-page.js started");

// Простые данные режимов
const MODES = [
  {
    id: "txt2img",
    title: "Генерация",
    desc: "Создание изображения по тексту",
    price: 4,
    image: "https://placehold.co/600x400/3aa0ff/ffffff?text=Text+to+Image",
  },
  {
    id: "img2img",
    title: "Смена стиля",
    desc: "Изменение стиля изображения",
    price: 4,
    image: "https://placehold.co/600x400/0a84ff/ffffff?text=Style+Transfer",
  },
];

// DOM элементы
const screenPick = document.getElementById("screenPick");
const screenGen = document.getElementById("screenGen");
const modeList = document.getElementById("modeList");

console.log("Elements found:", {
  screenPick: !!screenPick,
  screenGen: !!screenGen,
  modeList: !!modeList,
});

if (!screenPick || !modeList) {
  console.error("❌ Critical elements not found!");
  alert("Ошибка загрузки интерфейса");
}

// Показать экран выбора
function showPick() {
  if (screenPick && screenGen) {
    screenPick.classList.add("active");
    screenGen.classList.remove("active");
  }
}

// Показать экран генерации
function showGen(modeTitle) {
  if (screenPick && screenGen) {
    screenPick.classList.remove("active");
    screenGen.classList.add("active");
    
    const modeName = document.getElementById("modeName");
    if (modeName) modeName.textContent = modeTitle;
  }
}

// Построить список режимов
function buildModes() {
  if (!modeList) {
    console.error("modeList element not found");
    return;
  }
  
  modeList.innerHTML = "";
  
  MODES.forEach(mode => {
    const card = document.createElement("div");
    card.className = "modeCard";
    card.style.cssText = `
      width: 100%;
      height: 360px;
      border-radius: 22px;
      overflow: hidden;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      margin-bottom: 16px;
      cursor: pointer;
    `;
    
    card.innerHTML = `
      <div style="height:220px; overflow:hidden;">
        <img src="${mode.image}" alt="${mode.title}" style="width:100%; height:100%; object-fit:cover;">
      </div>
      <div style="padding:16px;">
        <div style="font-size:16px; font-weight:bold; color:white;">${mode.title}</div>
        <div style="font-size:13px; color:rgba(255,255,255,0.8); margin-top:4px;">${mode.desc}</div>
        <div style="font-size:18px; color:#ffd966; font-weight:bold; margin-top:10px;">${mode.price} ⭐</div>
      </div>
    `;
    
    card.onclick = () => {
      console.log("Mode selected:", mode.id);
      showGen(mode.title);
    };
    
    modeList.appendChild(card);
  });
}

// Инициализация
function init() {
  console.log("Initializing image page...");
  
  // Проверка Telegram WebApp
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    console.log("Telegram WebApp initialized");
  }
  
  // Построить режимы
  buildModes();
  
  // Показать экран выбора
  showPick();
  
  console.log("✅ Initialization complete");
}

// Запуск при загрузке
document.addEventListener("DOMContentLoaded", init);
window.addEventListener("load", init);

// Запуск сейчас (на случай если DOM уже загружен)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}