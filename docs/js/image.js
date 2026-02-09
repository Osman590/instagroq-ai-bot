// docs/js/image.js
// Главная логика вкладки генерации изображений

import { generateImage } from "./image-api.js";

// ====== КОНФИГУРАЦИЯ КАРТОЧЕК ======
export const MODES = {
  text: {
    id: "text",
    title: "Генерация по тексту",
    price: 4,
    needImage: false,
    needPrompt: true,
  },
  image: {
    id: "image",
    title: "Из картинки",
    price: 5,
    needImage: true,
    needPrompt: true,
  },
  removebg: {
    id: "removebg",
    title: "Удалить фон",
    price: 5,
    needImage: true,
    needPrompt: false,
  },
  upscale: {
    id: "upscale",
    title: "Улучшить качество",
    price: 6,
    needImage: true,
    needPrompt: false,
  },
};

// ====== СОСТОЯНИЕ ======
let currentMode = null;
let uploadedFile = null;
let lastPayload = null;

// ====== SETTERS ======
export function setMode(modeId) {
  currentMode = MODES[modeId] || null;
}

export function setImage(file) {
  uploadedFile = file || null;
}

export function clearImage() {
  uploadedFile = null;
}

// ====== ВАЛИДАЦИЯ ======
export function validate(promptText = "") {
  if (!currentMode) {
    return { ok: false, error: "Режим не выбран" };
  }

  if (currentMode.needImage && !uploadedFile) {
    return { ok: false, error: "Нужно выбрать изображение" };
  }

  if (currentMode.needPrompt && !promptText.trim()) {
    return { ok: false, error: "Введите описание" };
  }

  return { ok: true };
}

// ====== PAYLOAD ======
function buildPayload(promptText = "") {
  return {
    mode: currentMode.id,
    price: currentMode.price,
    prompt: promptText.trim() || null,
    image: uploadedFile || null,
  };
}

// ====== ГЕНЕРАЦИЯ ======
export async function runGeneration(promptText = "") {
  const check = validate(promptText);
  if (!check.ok) {
    throw new Error(check.error);
  }

  const payload = buildPayload(promptText);
  lastPayload = payload;

  const result = await generateImage(payload);
  return result;
}

// ====== ПОВТОР ======
export async function repeatGeneration() {
  if (!lastPayload) {
    throw new Error("Нет предыдущей генерации");
  }
  const result = await generateImage(lastPayload);
  return result;
}

// ====== HELPERS ======
export function getCurrentMode() {
  return currentMode;
}

export function resetAll() {
  currentMode = null;
  uploadedFile = null;
  lastPayload = null;
}