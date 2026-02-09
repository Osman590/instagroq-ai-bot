// docs/js/image.js
import { initVH } from "./image.vh.js";
import { initNav } from "./image.nav.js";
import { initImageUI } from "./image.ui.js";

const tg = window.Telegram?.WebApp || null;
const url = new URL(window.location.href);

initVH(tg);
initNav({ tg, url });
initImageUI({ tg, url });