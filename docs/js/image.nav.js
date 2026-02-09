// docs/js/image.nav.js
export function initNav({ tg, url } = {}){
  const backBtn = document.getElementById("backBtn");
  if (!backBtn) return;

  // keep lang/theme on back
  const lang = url.searchParams.get("lang") || (localStorage.getItem("miniapp_lang_v1") || "ru");
  const theme = url.searchParams.get("theme") || (localStorage.getItem("miniapp_theme_v1") || "blue");
  backBtn.href = "./index.html?lang=" + encodeURIComponent(lang) + "&theme=" + encodeURIComponent(theme);

  // smooth exit on back
  function smoothGo(href){
    document.body.classList.remove("pageIn");
    document.body.classList.add("pageOut");
    setTimeout(() => { window.location.href = href; }, 260);
  }

  backBtn.addEventListener("click", (e) => {
    e.preventDefault();
    smoothGo(backBtn.href);
  });
}