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

// ===== helpers =====
function showPick(){
  requestAnimationFrame(() => {
    screenPick.classList.add("active");
    screenGen.classList.remove("active");
  });
}

function showGen(){
  requestAnimationFrame(() => {
    screenPick.classList.remove("active");
    screenGen.classList.add("active");
  });
}

function modeNeedsFile(modeId){
  return modeId !== "txt2img";
}

function ensureHiddenWrap(el, hide){
  if (!el) return;
  if (hide) {
    el.classList.add("hidden");
    el.style.display = "none";
  } else {
    el.classList.remove("hidden");
    el.style.display = "";
  }
}

function syncRemoveButton(){
  const modeId = getMode()?.id || "";
  const file = getFile();

  if (modeId === "txt2img") {
    ensureHiddenWrap(removeImgBtn, true);
    return;
  }
  ensureHiddenWrap(removeImgBtn, !file);
}

function resetResult(){
  if (resultImg) resultImg.removeAttribute("src");
  outEl.classList.add("hidden");
}

function setGeneratingUI(isGen){
  const modeId = getMode()?.id || "";
  const needFile = modeNeedsFile(modeId);

  if (isGen) {
    if (promptEl) promptEl.style.display = "none";
    if (genBtn) genBtn.style.display = "none";
    if (changeModeBtn) changeModeBtn.style.display = "none";
    if (pickFileBtn) pickFileBtn.style.display = "none";
    if (previewWrap) ensureHiddenWrap(previewWrap, true);
    if (removeImgBtn) ensureHiddenWrap(removeImgBtn, true);

    loadingEl.classList.remove("hidden");
    outEl.classList.add("hidden");

    // 🔹 панель генерации всегда в том же месте
    loadingEl.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  if (promptEl) promptEl.style.display = "";
  if (genBtn) genBtn.style.display = "";
  if (changeModeBtn) changeModeBtn.style.display = "";

  if (pickFileBtn) pickFileBtn.style.display = needFile ? "" : "none";

  const file = getFile();
  if (needFile && file) ensureHiddenWrap(previewWrap, false);
  else ensureHiddenWrap(previewWrap, true);

  syncRemoveButton();
  loadingEl.classList.add("hidden");
}

function syncGenUIForMode(){
  const m = getMode();
  const modeId = m?.id || "";
  const needFile = modeNeedsFile(modeId);

  pickFileBtn.style.display = needFile ? "" : "none";

  if (!needFile) {
    setFile(null);
    if (previewImg) previewImg.removeAttribute("src");
    ensureHiddenWrap(previewWrap, true);
    fileInput.value = "";
  }

  loadingEl.classList.add("hidden");
  resetResult();
  syncRemoveButton();
  setGeneratingUI(false);
}

// ===== modes list =====
function buildModes(){
  modeList.innerHTML = "";

  for (const m of getModes()) {
    const card = document.createElement("div");
    card.className = "modeCard";

    card.innerHTML = `
      <div class="modeImg">
        <div class="imgLoader"></div>
        <img src="${m.image}" alt="${m.title}">
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
    img.onerror = () => {
      imgWrap.classList.add("error");
      console.error(`Failed to load mode image: ${m.image}`);
    };

    card.onclick = () => {
      setMode(m.id);
      modeName.textContent = m.title;
      syncGenUIForMode();
      showGen();
    };

    modeList.appendChild(card);
  }
}

// ===== file pick/remove =====
pickFileBtn.onclick = () => fileInput.click();

fileInput.onchange = () => {
  const file = fileInput.files[0];
  if (!file) return;
  
  // Проверка размера файла (макс 10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert("Файл слишком большой. Максимальный размер: 10MB");
    fileInput.value = "";
    return;
  }
  
  // Проверка типа файла
  if (!file.type.startsWith("image/")) {
    alert("Выберите файл изображения (JPG, PNG, etc.)");
    fileInput.value = "";
    return;
  }
  
  setFile(file);
  previewImg.src = URL.createObjectURL(file);
  ensureHiddenWrap(previewWrap, false);
  syncRemoveButton();
};

removeImgBtn.onclick = () => {
  setFile(null);
  if (previewImg) {
    // Освобождаем память от blob URL
    if (previewImg.src.startsWith("blob:")) {
      URL.revokeObjectURL(previewImg.src);
    }
    previewImg.removeAttribute("src");
  }
  fileInput.value = "";
  ensureHiddenWrap(previewWrap, true);
  syncRemoveButton();
};

// ===== change mode =====
changeModeBtn.onclick = () => {
  resetState();
  if (promptEl) promptEl.value = "";
  setFile(null);
  
  // Освобождаем память от blob URL
  if (previewImg && previewImg.src.startsWith("blob:")) {
    URL.revokeObjectURL(previewImg.src);
  }
  if (previewImg) previewImg.removeAttribute("src");
  
  fileInput.value = "";
  ensureHiddenWrap(previewWrap, true);
  loadingEl.classList.add("hidden");
  resetResult();
  syncRemoveButton();
  showPick();
};

// ===== generate =====
genBtn.onclick = async () => {
  const m = getMode();
  const modeId = m?.id || "";
  if (!modeId) {
    alert("Сначала выберите функцию");
    return;
  }

  const prompt = (promptEl?.value || "").trim();
  const file = getFile();

  if (modeNeedsFile(modeId) && !file) {
    alert("Для этого режима нужно выбрать фото");
    return;
  }
  
  if (modeId === "txt2img" && !prompt) {
    alert("Введите описание для генерации");
    return;
  }

  promptEl.blur();
  setGeneratingUI(true);
  genBtn.disabled = true;

  try {
    // Обновляем текст загрузки в зависимости от режима
    const modeNames = {
      "txt2img": "Генерация изображения...",
      "img2img": "Изменение стиля...",
      "remove_bg": "Удаление фона...",
      "inpaint": "Удаление объекта...",
      "upscale": "Улучшение качества..."
    };
    
    loadingEl.textContent = modeNames[modeId] || "⏳ Генерация...";

    const res = await generateImage({ prompt, mode: modeId, file });
    
    // Проверяем разные форматы ответа
    let imageSrc = null;
    if (res.image_base64) {
      imageSrc = res.image_base64;
    } else if (res.url) {
      imageSrc = res.url;
    } else if (res.image_url) {
      imageSrc = res.image_url;
    }
    
    if (!imageSrc) {
      throw new Error("Не получено изображение");
    }

    loadingEl.classList.add("hidden");
    resultImg.src = imageSrc;
    
    // Добавляем обработчик ошибок загрузки изображения
    resultImg.onerror = () => {
      outEl.classList.add("hidden");
      alert("Ошибка загрузки сгенерированного изображения");
    };
    
    resultImg.onload = () => {
      outEl.classList.remove("hidden");
      outEl.scrollIntoView({ behavior: "smooth", block: "center" });
    };
    
    // Показываем сразу, если onload не сработает
    setTimeout(() => {
      if (resultImg.complete) {
        outEl.classList.remove("hidden");
      }
    }, 1000);

  } catch (error) {
    loadingEl.classList.add("hidden");
    resetResult();
    setGeneratingUI(false);
    
    // Показываем сообщение об ошибке
    if (error.message) {
      alert(error.message);
    } else {
      alert("Ошибка генерации. Попробуйте позже.");
    }
    
    console.error("Generation error:", error);
    
  } finally {
    genBtn.disabled = false;
  }
};

// Инициализация
buildModes();
showPick();

// Обработка закрытия страницы - очищаем blob URLs
window.addEventListener("beforeunload", () => {
  if (previewImg && previewImg.src.startsWith("blob:")) {
    URL.revokeObjectURL(previewImg.src);
  }
  if (resultImg && resultImg.src.startsWith("blob:")) {
    URL.revokeObjectURL(resultImg.src);
  }
});