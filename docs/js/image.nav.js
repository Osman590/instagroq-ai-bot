// docs/js/image.nav.js
export function initNav() {
  // keep lang/theme on back
  const url = new URL(window.location.href);
  const lang = url.searchParams.get("lang") || (localStorage.getItem("miniapp_lang_v1") || "ru");
  const theme = url.searchParams.get("theme") || (localStorage.getItem("miniapp_theme_v1") || "blue");

  const backBtn = document.getElementById("backBtn");
  if (backBtn) {
    backBtn.href = "./index.html?lang=" + encodeURIComponent(lang) + "&theme=" + encodeURIComponent(theme);

    // плавный выход
    backBtn.addEventListener("click", (e) => {
      e.preventDefault();
      document.body.classList.add("pageLeave");
      const href = backBtn.href;
      setTimeout(() => { window.location.href = href; }, 220);
    });
  }
}