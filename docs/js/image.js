// docs/js/image.js

export const MODES = [
  {
    id: "style",
    title: "Смена стиля",
    desc: "Изменить художественный стиль изображения",
  },
  {
    id: "enhance",
    title: "Улучшение",
    desc: "Повысить качество и детализацию",
  },
  {
    id: "anime",
    title: "Аниме",
    desc: "Преобразовать изображение в аниме-стиль",
  },
  {
    id: "realistic",
    title: "Реализм",
    desc: "Сделать изображение более реалистичным",
  },
];

// состояние
let currentMode = null;
let selectedFile = null;

export function getModes() {
  return MODES;
}

export function setMode(modeId) {
  currentMode = MODES.find(m => m.id === modeId) || null;
}

export function getMode() {
  return currentMode;
}

export function setFile(file) {
  selectedFile = file || null;
}

export function getFile() {
  return selectedFile;
}

export function resetState() {
  currentMode = null;
  selectedFile = null;
}