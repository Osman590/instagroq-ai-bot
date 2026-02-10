export const MODES = [
  {
    id: "txt2img",
    title: "Генерация",
    desc: "Создание изображения по тексту",
    price: 4,
    image: "./assets/modes/0A407D03-2BC3-4080-9A8F-A7B1F05930E7.png",
  },
  {
    id: "img2img",
    title: "Смена стиля",
    desc: "Изменение стиля изображения",
    price: 4,
    image: "./assets/modes/27C098FB-D965-46E9-8B60-1A21AFE1FE5.png",
  },
  {
    id: "remove_bg",
    title: "Удалить фон",
    desc: "Автоматическое удаление фона",
    price: 6,
    image: "./assets/modes/F0BB89EF-5848-427F-AF43-30748899327E.png",
  },
  {
    id: "inpaint",
    title: "Удалить объект",
    desc: "Стереть объект на изображении",
    price: 6,
    image: "./assets/modes/474C4F0A-1E78-43D6-847F-692EECBFE0C2.png",
  },
  {
    id: "upscale",
    title: "Улучшить качество",
    desc: "Повысить разрешение изображения",
    price: 3,
    image: "./assets/modes/E6B3EE8C-A086-4E0A-B939-12D1A52879D1.png",
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