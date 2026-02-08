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

    // ✅ expand ТОЛЬКО для чата
    if (mode === "chat") {
      tg.expand();
    }

    // ❌ убираем swipe-to-close (iOS)
    if (tg.disableClosingConfirmation) {
      tg.disableClosingConfirmation();
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