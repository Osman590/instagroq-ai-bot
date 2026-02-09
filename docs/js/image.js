// docs/js/image.js
import { initVH } from "./image.vh.js";
import { initNav } from "./image.nav.js";
import { initImageUI } from "./image.ui.js";

initVH();
initNav();

// плавный вход страницы
document.body.classList.add("pageEnter");

initImageUI();