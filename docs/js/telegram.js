export const tg = window.Telegram?.WebApp || null;

/**
 * Устанавливает корректную высоту экрана
 */
export function applyViewportHeight() {
  if (tg && typeof tg.viewportHeight === "number") {
    document.documentElement.style.setProperty("--vh", tg.viewportHeight + "px");
  } else {
    document.documentElement.style.setProperty("--vh", window.innerHeight + "px");
  }
}

/**
 * Инициализация Telegram Mini App
 * mode: "menu" | "chat"
 */
export function initTelegramViewport({ chatEl = null, mode = "menu" } = {}) {
  if (tg) {
    tg.ready();

    // ✅ ВСЕГДА раскрываем мини-апп полностью (iOS fix)
    if (typeof tg.expand === "function") {
      tg.expand();
    }

    // ❌ убираем swipe-to-close (iOS)
    if (tg.disableClosingConfirmation) {
      tg.disableClosingConfirmation();
    }

    // ❌ убираем вертикальные свайпы (iOS, частичная высота)
    if (typeof tg.disableVerticalSwipes === "function") {
      tg.disableVerticalSwipes();
    }
  }

  applyViewportHeight();

  const onChange = () => {
    applyViewportHeight();

    // автоскролл только для чата
    if (chatEl) {
      requestAnimationFrame(() => {
        chatEl.scrollTop = chatEl.scrollHeight;
      });
    }
  };

  if (tg && tg.onEvent) {
    tg.onEvent("viewportChanged", onChange);
  } else {
    window.addEventListener("resize", onChange);
  }
}