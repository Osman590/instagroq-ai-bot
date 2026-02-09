// docs/js/image.vh.js
export function initVH() {
  const tg = window.Telegram?.WebApp;

  function applyVH(){
    if (tg && typeof tg.viewportHeight === "number") {
      document.documentElement.style.setProperty("--vh", tg.viewportHeight + "px");
    } else {
      document.documentElement.style.setProperty("--vh", window.innerHeight + "px");
    }
  }

  if (tg) {
    tg.ready();
    tg.expand();
    applyVH();
    tg.onEvent("viewportChanged", applyVH);
  } else {
    applyVH();
    window.addEventListener("resize", applyVH);
  }
}