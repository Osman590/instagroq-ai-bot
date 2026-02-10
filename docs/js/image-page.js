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

function ensureHiddenWrap(el, hide){
  if (!el) return;
  if (hide) {
    el.classList.add("hidden");
    el.style.display = "none";     // ✅ чтобы не оставался “квадрат”
  } else {
    el.classList.remove("hidden");
    el.style.display = "";         // вернуть как было
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
  // когда генерируем — прячем ВСЁ, оставляем только loading
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
    return;
  }

  // когда НЕ генерируем — показываем нужные элементы по режиму
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

  // показать/скрыть выбор фото по режиму
  pickFileBtn.style.display = needFile ? "" : "none";

  // txt2img — убираем фото и превью
  if (!needFile) {
    setFile(null);
    if (previewImg) previewImg.removeAttribute("src");
    ensureHiddenWrap(previewWrap, true);
    fileInput.value = "";
  }

  // сброс результата при переключении режима
  loadingEl.classList.add("hidden");
  resetResult();

  // “Удалить” — только когда реально есть файл и режим требует файл
  syncRemoveButton();

  // вернуть обычный UI (не режим генерации)
  setGeneratingUI(false);
}

// ===== UI: loading panel + buttons (создаём, если их нет в HTML) =====
function ensureLoadingPanel(){
  if (!loadingEl) return { timeEl: null, textEl: null };

  let panel = loadingEl.querySelector(".genPanel");
  if (!panel) {
    loadingEl.innerHTML = `
      <div class="genPanel">
        <div class="genSpinner" aria-hidden="true"></div>
        <div class="genText">Генерация...</div>
        <div class="genTime">~ <span class="genEta">--</span> сек</div>
      </div>
    `;
    panel = loadingEl.querySelector(".genPanel");
  }

  return {
    etaEl: loadingEl.querySelector(".genEta"),
    textEl: loadingEl.querySelector(".genText"),
  };
}

function ensureResultButtons(){
  if (!outEl) return { saveBtn: null, retryBtn: null };

  let btnRow = outEl.querySelector(".genBtnRow");
  if (!btnRow) {
    btnRow = document.createElement("div");
    btnRow.className = "genBtnRow";

    const save = document.createElement("button");
    save.type = "button";
    save.className = "genBtn genBtnSave";
    save.textContent = "Сохранить";

    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "genBtn genBtnRetry";
    retry.textContent = "Повторить";

    btnRow.appendChild(save);
    btnRow.appendChild(retry);
    outEl.appendChild(btnRow);
  }

  return {
    saveBtn: outEl.querySelector(".genBtnSave"),
    retryBtn: outEl.querySelector(".genBtnRetry"),
  };
}

function saveImage(src){
  if (!src) return;

  // если есть tg — открываем ссылку (на iOS это самый стабильный вариант)
  if (tg && typeof tg.openLink === "function") {
    tg.openLink(src);
    return;
  }

  // иначе пытаемся скачать через <a>
  const a = document.createElement("a");
  a.href = src;
  a.target = "_blank";
  a.rel = "noopener";
  a.download = "image.png";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function showNormalFormAfterResult(){
  // убрать результат и кнопки, вернуть форму
  resetResult();

  // вернуть UI по текущему режиму
  const modeId = getMode()?.id || "";
  const needFile = modeNeedsFile(modeId);

  if (promptEl) promptEl.style.display = "";
  if (genBtn) genBtn.style.display = "";
  if (changeModeBtn) changeModeBtn.style.display = "";

  if (pickFileBtn) pickFileBtn.style.display = needFile ? "" : "none";

  const file = getFile();
  if (needFile && file) ensureHiddenWrap(previewWrap, false);
  else ensureHiddenWrap(previewWrap, true);

  syncRemoveButton();
}

// ===== modes list =====
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

// ===== file pick/remove =====
pickFileBtn.onclick = () => fileInput.click();

fileInput.onchange = () => {
  const file = fileInput.files[0];
  if (!file) return;
  setFile(file);
  previewImg.src = URL.createObjectURL(file);
  ensureHiddenWrap(previewWrap, false);
  syncRemoveButton();
};

removeImgBtn.onclick = () => {
  // ✅ полностью убрать “квадрат” превью и файл
  setFile(null);
  if (previewImg) previewImg.removeAttribute("src");
  fileInput.value = "";
  ensureHiddenWrap(previewWrap, true);
  syncRemoveButton();
};

// ===== change mode =====
changeModeBtn.onclick = () => {
  resetState();

  // сброс UI
  if (promptEl) promptEl.value = "";
  setFile(null);

  if (previewImg) previewImg.removeAttribute("src");
  fileInput.value = "";
  ensureHiddenWrap(previewWrap, true);

  loadingEl.classList.add("hidden");
  resetResult();
  syncRemoveButton();

  showPick();
};

// ===== keyboard UX =====
// закрывать клавиатуру при тапе вне инпута/кнопок
screenGen.addEventListener("pointerdown", (e) => {
  if (!promptEl) return;

  const t = e.target;
  const isInsideInput = (t === promptEl) || (promptEl.contains && promptEl.contains(t));
  if (isInsideInput) return;

  // если тап по кнопкам — не мешаем
  if (t === genBtn || t === pickFileBtn || t === removeImgBtn || t === changeModeBtn) return;

  promptEl.blur();
});

// при фокусе — поднять экран, чтобы поле было видно
if (promptEl) {
  promptEl.addEventListener("focus", () => {
    setTimeout(() => {
      promptEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 350);
  });
}

// ===== generate =====
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

  // ===== UI: показать только квадратный лоадинг-панель =====
  promptEl.blur();
  setGeneratingUI(true);
  genBtn.disabled = true;

  const { etaEl, textEl } = ensureLoadingPanel();

  // таймер (если API не отдаёт ETA — показываем условные 20 сек)
  let secondsLeft = 20;
  let timerId = null;

  const startTimer = () => {
    if (!etaEl) return;
    etaEl.textContent = String(secondsLeft);
    timerId = setInterval(() => {
      secondsLeft = Math.max(0, secondsLeft - 1);
      etaEl.textContent = String(secondsLeft);
      if (secondsLeft <= 0) {
        clearInterval(timerId);
        timerId = null;
      }
    }, 1000);
  };

  startTimer();

  try {
    if (textEl) textEl.textContent = "Генерация...";

    const res = await generateImage({ prompt, mode: modeId, file });

    // если API вернул ETA — подстроимся
    const etaFromApi = Number(res?.eta_seconds || res?.eta || 0);
    if (etaFromApi > 0 && etaEl) {
      secondsLeft = Math.min(999, Math.round(etaFromApi));
      etaEl.textContent = String(secondsLeft);
    }

    const url = res?.image_url || res?.url || "";
    const b64 = res?.image_base64 || res?.base64 || "";
    const src = b64 || url;

    if (!src) throw new Error("no_image_in_response");

    // показать результат + кнопки
    if (timerId) { clearInterval(timerId); timerId = null; }

    loadingEl.classList.add("hidden");

    resultImg.src = src;
    outEl.classList.remove("hidden");

    const { saveBtn, retryBtn } = ensureResultButtons();

    if (saveBtn) {
      saveBtn.onclick = () => saveImage(src);
    }
    if (retryBtn) {
      retryBtn.onclick = () => {
        // убрать картинку и кнопки, вернуть форму
        if (resultImg) resultImg.removeAttribute("src");

        // спрятать кнопки (ряд)
        const row = outEl.querySelector(".genBtnRow");
        if (row) row.remove();

        showNormalFormAfterResult();
      };
    }

  } catch (e) {
    if (timerId) { clearInterval(timerId); timerId = null; }
    loadingEl.classList.add("hidden");
    resetResult();
    setGeneratingUI(false);
    alert("Ошибка генерации");
  } finally {
    genBtn.disabled = false;
  }
};

buildModes();
showPick();