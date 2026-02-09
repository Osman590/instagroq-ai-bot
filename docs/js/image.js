export const MODES = [
  {
    id: "txt2img",
    title: "Генерация",
    desc: "Создание изображения по тексту",
    price: 4,
    image: "./assets/modes/txt2img.jpg",
  },
  {
    id: "img2img",
    title: "Смена стиля",
    desc: "Изменение стиля изображения",
    price: 4,
    image: "./assets/modes/style.jpg",
  },
  {
    id: "remove_bg",
    title: "Удалить фон",
    desc: "Автоматическое удаление фона",
    price: 6,
    image: "./assets/modes/remove-bg.jpg",
  },
  {
    id: "inpaint",
    title: "Удалить объект",
    desc: "Стереть объект на изображении",
    price: 6,
    image: "./assets/modes/inpaint.jpg",
  },
  {
    id: "upscale",
    title: "Улучшить качество",
    desc: "Повысить разрешение изображения",
    price: 3,
    image: "./assets/modes/upscale.jpg",
  },
];

let currentMode = null;
let selectedFile = null;

export function getModes() {
  return MODES;
}

export function setMode(id) {
  currentMode = MODES.find(m => m.id === id) || null;
}

export function getMode() {
  return currentMode;
}

export function setFile(file) {
  selectedFile = file;
}

export function getFile() {
  return selectedFile;
}

export function resetState() {
  currentMode = null;
  selectedFile = null;
}