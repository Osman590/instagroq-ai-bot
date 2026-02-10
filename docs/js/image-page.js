// docs/js/image-page.js
import { getModes, setMode, getMode, setFile, getFile, resetState } from "./image.js";
import { generateImage } from "./image-api.js";

console.log("🚀 image-page.js started");

const tg = window.Telegram?.WebApp;

function applyVH(){
  const vh = (tg?.viewportHeight || window.innerHeight) + "px";
  document.documentElement.style.setProperty("--vh", vh);
  console.log("Viewport height:", vh);
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

// Получаем все элементы
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

console.log("Elements check:", {
  screenPick: !!screenPick,
  screenGen: !!screenGen,
  modeList: !!modeList,
  fileInput: !!fileInput,
  pickFileBtn: !!pickFileBtn,
  genBtn: !!genBtn,
});

// ===== helpers =====
function showPick(){
  console.log("Showing pick screen");
  if (screenPick && screenGen) {
    screenPick.classList.add("active");
    screenGen.classList.remove("active");
  }
}

function showGen(){
  console.log("Showing generation screen");
  if (screenPick && screenGen) {
    screenPick.classList.remove("active");
    screenGen.classList.add("active");
  }
}

function modeNeedsFile(modeId){
  return modeId !== "txt2img";
}

function updateUIForMode() {
  const mode = getMode();
  const modeId = mode?.id || "";
  const needsFile = modeNeedsFile(modeId);
  const hasFile = !!getFile();
  
  console.log("Updating UI for mode:", modeId, "needsFile:", needsFile, "hasFile:", hasFile);
  
  // Кнопка выбора файла
  if (pickFileBtn) {
    pickFileBtn.style.display = needsFile ? "" : "none";
  }
  
  // Preview изображения
  if (previewWrap) {
    if (needsFile && hasFile) {
      previewWrap.classList.remove("hidden");
    } else {
      previewWrap.classList.add("hidden");
    }
  }
  
  // Кнопка удаления
  if (removeImgBtn) {
    if (needsFile && hasFile) {
      removeImgBtn.classList.remove("hidden");
    } else {
      removeImgBtn.classList.add("hidden");
    }
  }
  
  // Поле промпта
  if (promptEl && modeId === "txt2img") {
    promptEl.placeholder = "Опишите что нужно сгенерировать...";
  } else if (promptEl) {
    promptEl.placeholder = "Опишите изменения...";
  }
}

// ===== modes list =====
function buildModes(){
  if (!modeList) {
    console.error("modeList element not found");
    return;
  }
  
  modeList.innerHTML = "";
  const modes = getModes();
  console.log("Building modes:", modes.length);
  
  modes.forEach(mode => {
    const card = document.createElement("div");
    card.className = "modeCard";
    
    card.innerHTML = `
      <div class="modeImg">
        <div class="imgLoader"></div>
        <img src="${mode.image}" alt="${mode.title}" onload="this.parentElement.classList.add('loaded')">
      </div>
      <div class="modeBody">
        <div class="modeTitle">${mode.title}</div>
        <div class="modeDesc">${mode.desc}</div>
        <div class="modePrice">${mode.price} ⭐</div>
      </div>
    `;
    
    card.onclick = () => {
      console.log("Mode selected:", mode.id);
      setMode(mode.id);
      if (modeName) modeName.textContent = mode.title;
      updateUIForMode();
      showGen();
    };
    
    modeList.appendChild(card);
  });
}

// ===== file pick/remove =====
if (pickFileBtn) {
  pickFileBtn.onclick = () => {
    console.log("Pick file clicked");
    if (fileInput) fileInput.click();
  };
}

if (fileInput) {
  fileInput.onchange = () => {
    const file = fileInput.files[0];
    console.log("File selected:", file?.name);
    if (!file) return;
    
    // Проверка
    if (!file.type.startsWith("image/")) {
      alert("Выберите файл изображения (JPG, PNG, etc.)");
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert("Файл слишком большой. Максимум 10MB");
      return;
    }
    
    setFile(file);
    if (previewImg) {
      previewImg.src = URL.createObjectURL(file);
    }
    updateUIForMode();
  };
}

if (removeImgBtn) {
  removeImgBtn.onclick = () => {
    console.log("Remove image clicked");
    setFile(null);
    if (previewImg) {
      URL.revokeObjectURL(previewImg.src);
      previewImg.src = "";
    }
    if (fileInput) fileInput.value = "";
    updateUIForMode();
  };
}

// ===== change mode =====
if (changeModeBtn) {
  changeModeBtn.onclick = () => {
    console.log("Change mode clicked");
    resetState();
    if (promptEl) promptEl.value = "";
    if (previewImg) {
      URL.revokeObjectURL(previewImg.src);
      previewImg.src = "";
    }
    if (fileInput) fileInput.value = "";
    if (loadingEl) loadingEl.classList.add("hidden");
    if (outEl) outEl.classList.add("hidden");
    if (resultImg) resultImg.src = "";
    updateUIForMode();
    showPick();
  };
}

// ===== generate =====
if (genBtn) {
  genBtn.onclick = async () => {
    console.log("Generate clicked");
    const mode = getMode();
    const modeId = mode?.id || "";
    
    if (!modeId) {
      alert("Сначала выберите функцию");
      return;
    }
    
    const prompt = (promptEl?.value || "").trim();
    const file = getFile();
    
    // Валидация
    if (modeNeedsFile(modeId) && !file) {
      alert("Для этого режима нужно выбрать фото");
      return;
    }
    
    if (modeId === "txt2img" && !prompt) {
      alert("Введите описание для генерации");
      return;
    }
    
    // Начало генерации
    console.log("Starting generation:", { modeId, promptLength: prompt.length, hasFile: !!file });
    
    if (promptEl) promptEl.disabled = true;
    if (genBtn) {
      genBtn.disabled = true;
      genBtn.textContent = "Генерация...";
    }
    
    if (loadingEl) {
      loadingEl.classList.remove("hidden");
      loadingEl.textContent = "⏳ Генерация изображения...";
    }
    
    if (outEl) outEl.classList.add("hidden");
    
    try {
      const result = await generateImage({ 
        prompt, 
        mode: modeId, 
        file 
      });
      
      console.log("Generation successful:", result);
      
      if (resultImg && result.image_base64) {
        resultImg.src = result.image_base64;
        resultImg.onload = () => {
          if (outEl) outEl.classList.remove("hidden");
          if (loadingEl) loadingEl.classList.add("hidden");
        };
      } else {
        throw new Error("No image in response");
      }
      
    } catch (error) {
      console.error("Generation error:", error);
      alert(error.message || "Ошибка генерации. Попробуйте позже.");
      
      if (loadingEl) loadingEl.classList.add("hidden");
      if (outEl) outEl.classList.add("hidden");
      
    } finally {
      if (promptEl) promptEl.disabled = false;
      if (genBtn) {
        genBtn.disabled = false;
        genBtn.textContent = "Сгенерировать";
      }
    }
  };
}

// ===== Инициализация =====
function init() {
  console.log("Initializing image page");
  buildModes();
  updateUIForMode();
  showPick();
  console.log("✅ Initialization complete");
}

// Запуск
document.addEventListener("DOMContentLoaded", init);
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  setTimeout(init, 100);
}