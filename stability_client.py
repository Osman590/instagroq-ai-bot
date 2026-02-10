# stability_client.py
import os
import base64
from typing import Optional

# --- ENV ---
STABILITY_API_KEY = (os.getenv("STABILITY_API_KEY") or "").strip()

# --- Stability Client ---
print(f"🔧 STABILITY_API_KEY loaded: {'Yes' if STABILITY_API_KEY else 'No'}")

def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    samples: int = 1,
) -> str:
    """
    Генерация изображения через Stability AI HTTP API.
    Возвращает base64 строку.
    """
    if not STABILITY_API_KEY:
        raise RuntimeError("STABILITY_API_KEY is not set")
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    # Используем Engine ID для SDXL
    engine_id = "stable-diffusion-xl-1024-v1-0"
    url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Подготовка промпта
    negative_prompt = negative_prompt or "blurry, low quality, distorted, ugly, bad anatomy, watermark, signature"
    
    payload = {
        "text_prompts": [
            {
                "text": prompt,
                "weight": 1.0
            },
            {
                "text": negative_prompt,
                "weight": -1.0
            }
        ],
        "cfg_scale": cfg_scale,
        "height": height,
        "width": width,
        "samples": samples,
        "steps": steps,
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            error_msg = f"Stability API error {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('name', 'Unknown')} - {error_data.get('message', 'No details')}"
            except:
                error_msg += f": {response.text[:200]}"
            raise RuntimeError(error_msg)
        
        data = response.json()
        
        if "artifacts" not in data or not data["artifacts"]:
            raise RuntimeError("No image generated")
        
        # Берем первую сгенерированную картинку
        image_base64 = data["artifacts"][0]["base64"]
        return f"data:image/png;base64,{image_base64}"
        
    except ImportError:
        raise RuntimeError("requests library is required")
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {str(e)}")


def generate_image_from_image(
    prompt: str,
    init_image: bytes,
    strength: float = 0.7,
    steps: int = 30,
    cfg_scale: float = 7.0,
) -> str:
    """
    Генерация изображения на основе другого изображения (img2img).
    Используем image-to-image API.
    """
    if not STABILITY_API_KEY:
        raise RuntimeError("STABILITY_API_KEY is not set")
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    if not init_image:
        raise ValueError("Init image is required")
    
    # Используем Engine ID для SDXL
    engine_id = "stable-diffusion-xl-1024-v1-0"
    url = f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json"
    }
    
    # Подготовка данных
    files = {
        "init_image": ("image.png", init_image, "image/png")
    }
    
    data = {
        "text_prompts[0][text]": prompt,
        "text_prompts[0][weight]": "1.0",
        "image_strength": str(strength),
        "cfg_scale": str(cfg_scale),
        "steps": str(steps),
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, files=files, data=data, timeout=90)
        
        if response.status_code != 200:
            error_msg = f"Stability img2img API error {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('name', 'Unknown')} - {error_data.get('message', 'No details')}"
            except:
                error_msg += f": {response.text[:200]}"
            raise RuntimeError(error_msg)
        
        data = response.json()
        
        if "artifacts" not in data or not data["artifacts"]:
            raise RuntimeError("No image generated from input")
        
        # Берем первую сгенерированную картинку
        image_base64 = data["artifacts"][0]["base64"]
        return f"data:image/png;base64,{image_base64}"
        
    except ImportError:
        raise RuntimeError("requests library is required")
    except Exception as e:
        raise RuntimeError(f"Image-to-image generation failed: {str(e)}")


# Функция для проверки доступности
def is_stability_available() -> bool:
    """Проверяет, доступен ли Stability AI клиент."""
    return bool(STABILITY_API_KEY)