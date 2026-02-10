// docs/js/image-api.js

const API_BASE = "https://instagroq-ai-bot-production.up.railway.app";
const API_IMAGE = API_BASE + "/api/image";

function getTelegramUser(){
  const tg = window.Telegram?.WebApp;
  if (!tg || !tg.initDataUnsafe?.user) return {};

  const u = tg.initDataUnsafe.user;
  return {
    tg_user_id: String(u.id || ""),
    tg_username: String(u.username || ""),
    tg_first_name: String(u.first_name || ""),
  };
}

export async function generateImage({ prompt, mode, file }) {
  const user = getTelegramUser();
  
  // Создаем FormData для отправки файла
  const form = new FormData();
  
  // Обязательные поля
  form.append("prompt", String(prompt || ""));
  form.append("mode", String(mode || "txt2img"));
  form.append("tg_user_id", user.tg_user_id);
  form.append("tg_username", user.tg_username);
  form.append("tg_first_name", user.tg_first_name);
  
  // Опциональные параметры (можно добавить настройки позже)
  form.append("steps", "30");
  form.append("cfg_scale", "7.0");
  form.append("width", "1024");
  form.append("height", "1024");
  
  // Добавляем файл если есть
  if (file) {
    form.append("image", file);
    
    // Настройки в зависимости от режима
    if (mode === "img2img") {
      form.append("strength", "0.7");
    } else if (mode === "remove_bg") {
      form.append("strength", "0.6");
    } else if (mode === "inpaint") {
      form.append("strength", "0.8");
    } else if (mode === "upscale") {
      form.append("strength", "0.5");
    }
  }
  
  try {
    const r = await fetch(API_IMAGE, {
      method: "POST",
      body: form,
      // Не устанавливаем Content-Type вручную - браузер сам установит с boundary
    });
    
    if (!r.ok) {
      const errorText = await r.text();
      console.error("Image API error:", r.status, errorText);
      
      // Пробуем распарсить JSON ошибки
      try {
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.error || `API error ${r.status}`);
      } catch {
        throw new Error(`API error ${r.status}: ${errorText.substring(0, 100)}`);
      }
    }
    
    const data = await r.json();
    
    // Проверяем успешность ответа
    if (data.error) {
      throw new Error(data.error);
    }
    
    if (!data.image_base64 && !data.url) {
      throw new Error("No image data received");
    }
    
    return data;
    
  } catch (error) {
    console.error("Generate image error:", error);
    
    // Более информативные сообщения об ошибках
    const errorMsg = error.message || "Unknown error";
    
    if (errorMsg.includes("payment_required") || errorMsg.includes("insufficient_balance")) {
      throw new Error("Недостаточно средств. Пополните баланс.");
    } else if (errorMsg.includes("blocked")) {
      throw new Error("Доступ заблокирован. Обратитесь к администратору.");
    } else if (errorMsg.includes("empty_prompt")) {
      throw new Error("Введите описание для генерации.");
    } else if (errorMsg.includes("image_required")) {
      throw new Error("Выберите изображение для этого режима.");
    } else if (errorMsg.includes("generation_timeout")) {
      throw new Error("Таймаут генерации. Попробуйте позже.");
    } else if (errorMsg.includes("invalid_api_key")) {
      throw new Error("Ошибка сервиса генерации. Сообщите администратору.");
    } else {
      throw new Error("Ошибка генерации: " + errorMsg.substring(0, 80));
    }
  }
}