export const MODES = [
  {
    id: "txt2img",
    title: "Генерация",
    desc: "Создание изображения по тексту",
    price: 4,
    image: "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjM2FhMGZmIi8+CiAgPGcgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyNCI+CiAgICA8dGV4dCB4PSI1MCUiIHk9IjQwJSI+R2VuZXJhdGlvbjwvdGV4dD4KICAgIDx0ZXh0IHg9IjUwJSIgeT0iNTAlIj5UZXh0IHRvIEltYWdlPC90ZXh0PgogIDwvZz4KPC9zdmc+",
  },
  {
    id: "img2img",
    title: "Смена стиля",
    desc: "Изменение стиля изображения",
    price: 4,
    image: "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMGE4NGZmIi8+CiAgPGcgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyNCI+CiAgICA8dGV4dCB4PSI1MCUiIHk9IjQwJSI+U3R5bGUgVHJhbnNmZXI8L3RleHQ+CiAgICA8dGV4dCB4PSI1MCUiIHk9IjUwJSI+SW1hZ2UgdG8gSW1hZ2U8L3RleHQ+CiAgPC9nPgo8L3N2Zz4=",
  },
  {
    id: "remove_bg",
    title: "Удалить фон",
    desc: "Автоматическое удаление фона",
    price: 6,
    image: "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMmZkNmEzIi8+CiAgPGcgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcrialIiBmb250LXNpemU9IjI0Ij4KICAgIDx0ZXh0IHg9IjUwJSIgeT0iNDAlIj5SZW1vdmUgQmFja2dyb3VuZDwvdGV4dD4KICAgIDx0ZXh0IHg9IjUwJSIgeT0iNTAlIj5CZyBSZW1vdmFsPC90ZXh0PgogIDwvZz4KPC9zdmc+",
  },
  {
    id: "inpaint",
    title: "Удалить объект",
    desc: "Стереть объект на изображении",
    price: 6,
    image: "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjYjk4Y2ZmIi8+CiAgPGcgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcrialIiBmb250LXNpemU9IjI0Ij4KICAgIDx0ZXh0IHg9IjUwJSIgeT0iNDAlIj5JbnBhaW50aW5nPC90ZXh0PgogICAgPHRleHQgeD0iNTAlIiB5PSI1MCUiPlJlbW92ZSBPYmplY3Q8L3RleHQ+CiAgPC9nPgo8L3N2Zz4=",
  },
  {
    id: "upscale",
    title: "Улучшить качество",
    desc: "Повысить разрешение изображения",
    price: 3,
    image: "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjN2ZiMmZmIi8+CiAgPGcgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcrialIiBmb250LXNpemU9IjI0Ij4KICAgIDx0ZXh0IHg9IjUwJSIgeT0iNDAlIj5VcHNjYWxpbmc8L3RleHQ+CiAgICA8dGV4dCB4PSI1MCUiIHk9IjUwJSI+RW5oYW5jZSBRdWFsaXR5PC90ZXh0PgogIDwvZz4KPC9zdmc+",
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