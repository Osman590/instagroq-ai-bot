import { initTelegramViewport } from "./telegram.js";
import { createChatController } from "./chat.js";
import { initSettingsUI } from "./settings.js";

const tg = window.Telegram?.WebApp || null;

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("text");
const sendBtnEl = document.getElementById("sendBtn");

/* ================================
   ✅ FIX: iOS keyboard + no “pull down”
   - всегда считаем реальную видимую высоту (visualViewport)
   - запрещаем “резинку” страницы, но оставляем скролл в чате
================================== */

function applyVH() {
  // 1) Самое точное на iOS при клавиатуре
  const vv = window.visualViewport;
  const h = vv && typeof vv.height === "number"
    ? vv.height
    : (tg && typeof tg.viewportHeight === "number"
        ? tg.viewportHeight
        : window.innerHeight);

  document.documentElement.style.setProperty("--vh", h + "px");
}

// обновления при любых изменениях viewport/клавиатуры
applyVH();

if (window.visualViewport) {
  // на iOS бывает “скачок” ещё и от scroll visualViewport
  window.visualViewport.addEventListener("resize", applyVH);
  window.visualViewport.addEventListener("scroll", applyVH);
}

window.addEventListener("resize", applyVH);

// Telegram events (если доступны)
if (tg) {
  try { tg.ready(); } catch(e) {}
  try { tg.expand(); } catch(e) {}

  // в некоторых версиях TG это реально блокирует “свайп вниз” WebView
  if (typeof tg.disableVerticalSwipes === "function") {
    try { tg.disableVerticalSwipes(); } catch(e) {}
  }

  if (typeof tg.onEvent === "function") {
    try { tg.onEvent("viewportChanged", applyVH); } catch(e) {}
  }
}

// ✅ Блокируем “резинку”/сдвиг страницы при свайпе
// но разрешаем прокрутку внутри .chat
let touchStartY = 0;

document.addEventListener("touchstart", (e) => {
  if (!e.touches || !e.touches[0]) return;
  touchStartY = e.touches[0].clientY;
}, { passive: true });

document.addEventListener("touchmove", (e) => {
  // разрешаем только если жест внутри чата
  const inChat = chatEl && e.target && (e.target === chatEl || chatEl.contains(e.target));
  if (!inChat) {
    e.preventDefault();
    return;
  }

  // внутри чата — дополнительно убираем “резинку” на краях
  const el = chatEl;
  if (!el) return;

  const currentY = e.touches[0].clientY;
  const dy = currentY - touchStartY;

  const atTop = el.scrollTop <= 0;
  const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1;

  // если тянем вниз на самом верху или вверх на самом низу — запрещаем, чтобы не “тянуло” страницу
  if ((atTop && dy > 0) || (atBottom && dy < 0)) {
    e.preventDefault();
  }
}, { passive: false });

/* ================================
   ✅ ТВОЙ ОРИГИНАЛ — НЕ ТРОГАЕМ
================================== */

const controller = createChatController({ chatEl, inputEl, sendBtnEl });

// оставляем как было (просто теперь vh уже корректный)
initTelegramViewport(chatEl);

controller.bindUI();
initSettingsUI({ controller });
controller.renderFromHistory();