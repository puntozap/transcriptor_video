import base64
import os
import requests


GEMINI_IMAGE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generar_background_texto(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "9:16",
    api_key: str | None = None,
    model: str | None = None,
    log_fn=None,
) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("El prompt no puede estar vacio.")
    if api_key is None or not str(api_key).strip():
        api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env.")
    model = model or os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

    if log_fn:
        log_fn(f"IA Fondo: Generando imagen ({model}, {aspect_ratio})...")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt.strip()}
                ]
            }
        ],
        "generationConfig": {
            "imageConfig": {
                "aspectRatio": aspect_ratio
            }
        }
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key.strip(),
    }
    url = GEMINI_IMAGE_URL.format(model=model)
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Respuesta sin candidatos de imagen.")
    parts = candidates[0].get("content", {}).get("parts") or []

    image_b64 = ""
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data") or {}
        image_b64 = inline.get("data") or ""
        if image_b64:
            break
    if not image_b64:
        raise RuntimeError("No se recibio imagen en la respuesta.")

    img_bytes = base64.b64decode(image_b64)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    if log_fn:
        log_fn(f"IA Fondo: Imagen lista -> {output_path}")
    return output_path
