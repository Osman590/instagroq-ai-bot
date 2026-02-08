import { initTelegramViewport } from "./telegram.js";
import { createChatController } from "./chat.js";
import { initSettingsUI } from "./settings.js";

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("text");
const sendBtnEl = document.getElementById("sendBtn");

const controller = createChatController({ chatEl, inputEl, sendBtnEl });

// ✅ FIX: правильный вызов + режим чата (expand + правильный vh при клавиатуре)
initTelegramViewport({ chatEl, mode: "chat" });

controller.bindUI();
initSettingsUI({ controller });
controller.renderFromHistory();