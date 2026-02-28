import base64
import os
import io
import requests
from PIL import Image


OPENAI_IMAGE_URL = "https://api.openai.com/v1/images/generations"


def _save_jpg_under_size(img_bytes: bytes, output_path: str, max_kb: int, log_fn=None) -> None:
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    max_bytes = max_kb * 1024
    quality = 95
    scale = 1.0

    while True:
        temp_img = img
        if scale < 1.0:
            w = max(1, int(img.width * scale))
            h = max(1, int(img.height * scale))
            temp_img = img.resize((w, h), Image.LANCZOS)

        buf = io.BytesIO()
        temp_img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        size = buf.tell()

        if size <= max_bytes:
            with open(output_path, "wb") as f:
                f.write(buf.getvalue())
            if log_fn:
                log_fn(f"OpenAI Imagen: JPG listo ({size // 1024} KB).")
            return

        if quality > 70:
            quality -= 5
            continue
        if quality > 40:
            quality -= 5
            continue

        if scale > 0.6:
            scale -= 0.05
            quality = 90
            continue

        # Fallback: save even if still large
        with open(output_path, "wb") as f:
            f.write(buf.getvalue())
        if log_fn:
            log_fn(f"OpenAI Imagen: JPG guardado pero excede {max_kb} KB.")
        return


def generar_background_openai(
    prompt: str,
    output_path: str,
    size: str = "1024x1536",
    quality: str = "medium",
    api_key: str | None = None,
    model: str = "gpt-image-1",
    log_fn=None,
) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("El prompt no puede estar vacio.")
    if api_key is None or not str(api_key).strip():
        api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en el .env.")

    payload = {
        "model": model,
        "prompt": prompt.strip(),
        "size": size,
        "quality": quality,
        "output_format": "jpeg",
        "output_compression": 80,
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    if log_fn:
        log_fn(f"OpenAI Imagen: Generando ({model}, {size}, {quality})...")
    resp = requests.post(OPENAI_IMAGE_URL, headers=headers, json=payload, timeout=90)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    b64 = data.get("data", [{}])[0].get("b64_json", "")
    if not b64:
        raise RuntimeError("No se recibio imagen en la respuesta.")

    img_bytes = base64.b64decode(b64)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    _save_jpg_under_size(img_bytes, output_path, max_kb=500, log_fn=log_fn)
    if log_fn:
        log_fn(f"OpenAI Imagen: Imagen lista -> {output_path}")
    return output_path
