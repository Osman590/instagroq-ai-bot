export const tg = window.Telegram?.WebApp || null;

export function applyViewportHeight() {
  if (tg && typeof tg.viewportHeight === "number") {
    document.documentElement.style.setProperty("--vh", tg.viewportHeight + "px");
  } else {
    document.documentElement.style.setProperty("--vh", window.innerHeight + "px");
  }
}

export function initTelegramViewport(chatEl = null) {
  if (tg) {
    tg.ready();
    tg.expand();
  }

  applyViewportHeight();

  const onChange = () => {
    applyViewportHeight();
    if (chatEl) requestAnimationFrame(() => (chatEl.scrollTop = chatEl.scrollHeight));
  };

  if (tg && tg.onEvent) {
    tg.onEvent("viewportChanged", onChange);
  } else {
    window.addEventListener("resize", onChange);
  }
}