# stability_client.py
import os
import io
import base64
from typing import Optional

# ---------- ENV ----------
STABILITY_API_KEY = (os.getenv("STABILITY_API_KEY") or "").strip()

# ---------- Stability Client ----------
stability_client = None

if STABILITY_API_KEY:
    try:
        from stability_sdk import client
        import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
        
        stability_client = client.StabilityInference(
            key=STABILITY_API_KEY,
            verbose=False,
            engine="stable-diffusion-xl-1024-v1-0",  # или другой engine
        )
        print("✅ Stability AI client initialized")
    except ImportError:
        print("⚠️ stability-sdk not installed. Run: pip install stability-sdk")
    except Exception as e:
        print(f"⚠️ Stability client init error: {e}")
else:
    print("⚠️ STABILITY_API_KEY is not set")


# ---------- Image Generation ----------
def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    samples: int = 1,
) -> Optional[str]:
    """
    Генерация изображения через Stability AI.
    Возвращает base64 строку или None при ошибке.
    """
    if not stability_client:
        raise RuntimeError("STABILITY_API_KEY is not set or client not initialized")
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    try:
        # Подготовка промпта
        negative_prompt = negative_prompt or "blurry, low quality, distorted, ugly, bad anatomy, watermark, signature"
        
        # Генерация
        answers = stability_client.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
            samples=samples,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )
        
        # Обработка ответа
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img_bytes = artifact.binary
                    # Конвертируем в base64 для фронтенда
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    return f"data:image/png;base64,{img_base64}"
        
        return None
        
    except Exception as e:
        print(f"❌ Stability generation error: {e}")
        raise


def generate_image_from_image(
    prompt: str,
    init_image: bytes,
    strength: float = 0.7,
    steps: int = 30,
    cfg_scale: float = 7.0,
) -> Optional[str]:
    """
    Генерация изображения на основе другого изображения (img2img).
    """
    if not stability_client:
        raise RuntimeError("STABILITY_API_KEY is not set or client not initialized")
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    if not init_image:
        raise ValueError("Init image is required")
    
    try:
        # Генерация с начальным изображением
        answers = stability_client.generate(
            prompt=prompt,
            init_image=init_image,
            start_schedule=1.0 - strength,  # 1 - strength
            steps=steps,
            cfg_scale=cfg_scale,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )
        
        # Обработка ответа
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img_bytes = artifact.binary
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    return f"data:image/png;base64,{img_base64}"
        
        return None
        
    except Exception as e:
        print(f"❌ Stability img2img error: {e}")
        raise