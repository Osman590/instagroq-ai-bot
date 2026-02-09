import { tg } from "./telegram.js";

export function initSettingsUI({ controller }) {
  const overlay = document.getElementById("overlay");
  const gearBtn = document.getElementById("gearBtn");
  const closeSettings = document.getElementById("closeSettings");
  const clearBtn = document.getElementById("clearBtn");
  const styleSel = document.getElementById("styleSel");
  const personaSel = document.getElementById("personaSel");
  const input = document.getElementById("text");

  // init style/persona
  styleSel.value = localStorage.getItem("ai_style") || "steps";
  personaSel.value = localStorage.getItem("ai_persona") || "friendly";

  gearBtn.addEventListener("click", () => {
    overlay.style.display = "flex";
    input?.blur();
  });

  closeSettings.addEventListener("click", () => (overlay.style.display = "none"));
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.style.display = "none";
  });

  styleSel.addEventListener("change", () => {
    localStorage.setItem("ai_style", styleSel.value);
  });

  personaSel.addEventListener("change", () => {
    localStorage.setItem("ai_persona", personaSel.value);
  });

  clearBtn.addEventListener("click", async () => {
    const ok = await controller.confirmClear();
    if (!ok) return;

    controller.clearHistory();
    overlay.style.display = "none";
  });
}