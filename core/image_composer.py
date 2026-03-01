
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps


def _parse_hex_color(value: str, fallback: str = "#FFFFFF") -> Tuple[int, int, int, int]:
    text = (value or fallback).strip()
    if not text:
        text = fallback
    if text.startswith("#"):
        text = text[1:]
    if len(text) == 3:
        text = "".join([c * 2 for c in text])
    if len(text) not in (6, 8):
        text = fallback.lstrip("#")
    try:
        r = int(text[0:2], 16)
        g = int(text[2:4], 16)
        b = int(text[4:6], 16)
        a = int(text[6:8], 16) if len(text) == 8 else 255
        return (r, g, b, a)
    except Exception:
        return (255, 255, 255, 255)


def _open_image(path: str) -> Image.Image | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    img = Image.open(p)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img


def _resize_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    iw, ih = img.size
    if iw == 0 or ih == 0:
        return img
    scale = max(target_w / iw, target_h / ih)
    nw = max(1, int(iw * scale))
    nh = max(1, int(ih * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    left = max(0, (nw - target_w) // 2)
    top = max(0, (nh - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _resize_contain(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    iw, ih = img.size
    if iw == 0 or ih == 0:
        return img
    scale = min(target_w / iw, target_h / ih)
    nw = max(1, int(iw * scale))
    nh = max(1, int(ih * scale))
    return img.resize((nw, nh), Image.LANCZOS)


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _paste_centered(canvas: Image.Image, layer: Image.Image, center_x: int, center_y: int) -> None:
    x = int(center_x - layer.width / 2)
    y = int(center_y - layer.height / 2)
    canvas.alpha_composite(layer, (x, y))


def _text_block_size(lines: list[str], font: ImageFont.ImageFont, line_spacing: int) -> tuple[int, int, list[int]]:
    widths = []
    heights = []
    for line in lines:
        bbox = font.getbbox(line) if hasattr(font, "getbbox") else None
        if bbox:
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        else:
            w, h = font.getsize(line)
        widths.append(w)
        heights.append(h)
    if not widths:
        return 0, 0, []
    total_h = sum(heights) + line_spacing * (len(heights) - 1)
    max_w = max(widths)
    return max_w, total_h, heights


def _draw_centered_multiline(text: str, font: ImageFont.ImageFont, color, width: int, height: int, line_spacing: int) -> Image.Image:
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    lines = text.splitlines()
    max_w, total_h, heights = _text_block_size(lines, font, line_spacing)
    if max_w == 0:
        return layer
    y = int((height - total_h) / 2)
    for i, line in enumerate(lines):
        bbox = font.getbbox(line) if hasattr(font, "getbbox") else None
        if bbox:
            w = bbox[2] - bbox[0]
        else:
            w, _ = font.getsize(line)
        x = int((width - w) / 2)
        draw.text((x, y), line, font=font, fill=color)
        y += heights[i] + line_spacing
    return layer


def _blend_channel(c1: int, c2: int, t: float) -> int:
    return int(c1 + (c2 - c1) * t)


def _make_gradient_layer(width: int, height: int, color1, color2, direction: str) -> Image.Image:
    if direction == "solid":
        return Image.new("RGBA", (width, height), color1)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = layer.load()
    r1, g1, b1, a1 = color1
    r2, g2, b2, a2 = color2
    if direction == "horizontal":
        denom = max(1, width - 1)
        for x in range(width):
            t = x / denom
            r = _blend_channel(r1, r2, t)
            g = _blend_channel(g1, g2, t)
            b = _blend_channel(b1, b2, t)
            a = _blend_channel(a1, a2, t)
            for y in range(height):
                pixels[x, y] = (r, g, b, a)
    elif direction == "diagonal":
        denom = max(1, (width - 1) + (height - 1))
        for y in range(height):
            for x in range(width):
                t = (x + y) / denom
                r = _blend_channel(r1, r2, t)
                g = _blend_channel(g1, g2, t)
                b = _blend_channel(b1, b2, t)
                a = _blend_channel(a1, a2, t)
                pixels[x, y] = (r, g, b, a)
    else:
        denom = max(1, height - 1)
        for y in range(height):
            t = y / denom
            r = _blend_channel(r1, r2, t)
            g = _blend_channel(g1, g2, t)
            b = _blend_channel(b1, b2, t)
            a = _blend_channel(a1, a2, t)
            for x in range(width):
                pixels[x, y] = (r, g, b, a)
    return layer

def compose_image(settings: dict, size: Tuple[int, int], preview_scale: float = 1.0) -> Image.Image:
    base_w, base_h = size
    if preview_scale and preview_scale != 1.0:
        base_w = max(1, int(base_w * preview_scale))
        base_h = max(1, int(base_h * preview_scale))

    transparent_bg = bool(settings.get("transparent_bg", False))
    canvas_bg = (0, 0, 0, 0) if transparent_bg else (0, 0, 0, 255)
    canvas = Image.new("RGBA", (base_w, base_h), canvas_bg)
    draw = ImageDraw.Draw(canvas)

    # Fondo
    bg_path = settings.get("background_path")
    bg_img = _open_image(bg_path)
    rect_enabled = bool(settings.get("rect_enabled", False))
    if not transparent_bg and (rect_enabled or not bg_img):
        rect_color1 = _parse_hex_color(settings.get("rect_color_1", "#3B2F2F"))
        rect_color2 = _parse_hex_color(settings.get("rect_color_2", "#A67C52"))
        rect_gradient = (settings.get("rect_gradient") or "vertical").lower()
        rect_layer = _make_gradient_layer(base_w, base_h, rect_color1, rect_color2, rect_gradient)
        rect_opacity = float(settings.get("rect_opacity", 1.0))
        rect_opacity = max(0.0, min(1.0, rect_opacity))
        if rect_opacity < 1.0:
            alpha = rect_layer.getchannel("A").point(lambda p: int(p * rect_opacity))
            rect_layer.putalpha(alpha)
        canvas.alpha_composite(rect_layer)
    if bg_img and not transparent_bg:
        bg_layer = _resize_cover(bg_img, base_w, base_h)
        bg_filter = (settings.get("bg_filter") or "none").lower()
        if bg_filter != "none":
            intensity = float(settings.get("bg_filter_intensity", 0.7))
            intensity = max(0.0, min(1.0, intensity))
            bg_layer = apply_bg_filter(bg_layer, bg_filter, intensity)
        canvas.alpha_composite(bg_layer)

    # Imagen principal
    if settings.get("main_enabled", True):
        main_path = settings.get("main_path")
        main_img = _open_image(main_path)
        if main_img:
            target_height = float(settings.get("main_height_pct", 0.6))
            target_height = max(0.05, min(0.95, target_height))
            target_h = max(1, int(base_h * target_height))
            target_w = max(1, int(base_w * target_height))
            main_layer = _resize_contain(main_img, target_w, target_h)
            scale = float(settings.get("main_scale", 1.0))
            if scale and scale != 1.0:
                nw = max(1, int(main_layer.width * scale))
                nh = max(1, int(main_layer.height * scale))
                main_layer = main_layer.resize((nw, nh), Image.LANCZOS)
            x_pct = float(settings.get("main_x_pct", 0.5))
            y_pct = float(settings.get("main_y_pct", 0.35))
            x = int(base_w * x_pct - main_layer.width / 2)
            y = int(base_h * y_pct - main_layer.height / 2)
            rotation = float(settings.get("main_rotation", 0.0))
            if rotation:
                main_layer = main_layer.rotate(rotation, expand=True, resample=Image.BICUBIC)
            _paste_centered(canvas, main_layer, int(base_w * x_pct), int(base_h * y_pct))

    # Texto superior (badge)
    if settings.get("top_enabled", False):
        top_text = (settings.get("top_text") or "").strip()
        top_text_2 = (settings.get("top_text_2") or "").strip()
        if top_text:
            font_size = int(float(settings.get("top_font_size", 64)) * preview_scale)
            font = _load_font(settings.get("font_bold"), max(10, font_size))
            text_color = _parse_hex_color(settings.get("top_text_color", "#FFFFFF"))
            bg_color = _parse_hex_color(settings.get("top_bg_color", "#E53935"))
            padding_x = int(24 * preview_scale)
            padding_y = int(18 * preview_scale)
            radius = int(22 * preview_scale)
            bbox = draw.textbbox((0, 0), top_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            box_w = text_w + padding_x * 2
            box_h = text_h + padding_y * 2
            top_y_pct = float(settings.get("top_y_pct", 0.08))
            box_x = int((base_w - box_w) / 2)
            box_y = int(base_h * top_y_pct)
            badge = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
            badge_draw = ImageDraw.Draw(badge)
            badge_draw.rounded_rectangle((0, 0, box_w, box_h), radius=radius, fill=bg_color)
            text_x = (box_w - text_w) // 2
            text_y = (box_h - text_h) // 2
            badge_draw.text((text_x, text_y), top_text, font=font, fill=text_color)
            rotation = float(settings.get("top_rotation", 0.0))
            if rotation:
                badge = badge.rotate(rotation, expand=True, resample=Image.BICUBIC)
            _paste_centered(canvas, badge, int(base_w / 2), int(box_y + box_h / 2))
            if top_text_2:
                text_color_2 = _parse_hex_color(settings.get("top2_text_color", "#FFE9B3"))
                bg_color_2 = _parse_hex_color(settings.get("top2_bg_color", "#E53935"))
                bbox2 = draw.textbbox((0, 0), top_text_2, font=font)
                text_w2 = bbox2[2] - bbox2[0]
                text_h2 = bbox2[3] - bbox2[1]
                box_w2 = text_w2 + padding_x * 2
                box_h2 = text_h2 + padding_y * 2
                gap_pct = float(settings.get("top_gap_pct", 0.04))
                gap_px = int(base_h * gap_pct)
                box_x2 = int((base_w - box_w2) / 2)
                box_y2 = box_y + box_h + gap_px
                badge2 = Image.new("RGBA", (box_w2, box_h2), (0, 0, 0, 0))
                badge2_draw = ImageDraw.Draw(badge2)
                badge2_draw.rounded_rectangle((0, 0, box_w2, box_h2), radius=radius, fill=bg_color_2)
                text_x2 = (box_w2 - text_w2) // 2
                text_y2 = (box_h2 - text_h2) // 2
                badge2_draw.text((text_x2, text_y2), top_text_2, font=font, fill=text_color_2)
                rotation2 = float(settings.get("top2_rotation", 0.0))
                if rotation2:
                    badge2 = badge2.rotate(rotation2, expand=True, resample=Image.BICUBIC)
                _paste_centered(canvas, badge2, int(base_w / 2), int(box_y2 + box_h2 / 2))

    # Titulo
    title_text = (settings.get("title_text") or "").strip()
    if title_text and settings.get("title_enabled", True):
        font_size = int(float(settings.get("title_font_size", 64)) * preview_scale)
        font = _load_font(settings.get("font_bold"), max(10, font_size))
        color = _parse_hex_color(settings.get("title_color", "#FFFFFF"))
        title_y_pct = float(settings.get("title_y_pct", 0.58))
        line_spacing = int(font_size * 0.2)
        max_w = int(base_w * 0.9)
        temp = _draw_centered_multiline(title_text, font, color, max_w, int(base_h * 0.25), line_spacing)
        rotation = float(settings.get("title_rotation", 0.0))
        if rotation:
            temp = temp.rotate(rotation, expand=True, resample=Image.BICUBIC)
        _paste_centered(canvas, temp, base_w // 2, int(base_h * title_y_pct))

    # Nombre
    name_text = (settings.get("name_text") or "").strip()
    if name_text and settings.get("name_enabled", True):
        font_size = int(float(settings.get("name_font_size", 48)) * preview_scale)
        font = _load_font(settings.get("font_regular"), max(10, font_size))
        color = _parse_hex_color(settings.get("name_color", "#FFFFFF"))
        name_y_pct = float(settings.get("name_y_pct", 0.68))
        line_spacing = int(font_size * 0.2)
        max_w = int(base_w * 0.9)
        temp = _draw_centered_multiline(name_text, font, color, max_w, int(base_h * 0.2), line_spacing)
        rotation = float(settings.get("name_rotation", 0.0))
        if rotation:
            temp = temp.rotate(rotation, expand=True, resample=Image.BICUBIC)
        _paste_centered(canvas, temp, base_w // 2, int(base_h * name_y_pct))

    # Logo
    if settings.get("logo_enabled", True):
        logo_path = settings.get("logo_path")
        logo_img = _open_image(logo_path)
        if logo_img:
            logo_width_pct = float(settings.get("logo_width_pct", 0.2))
            logo_width_pct = max(0.05, min(0.5, logo_width_pct))
            target_w = max(1, int(base_w * logo_width_pct))
            target_h = max(1, int(base_h * logo_width_pct))
            logo_layer = _resize_contain(logo_img, target_w, target_h)
            scale = float(settings.get("logo_scale", 1.0))
            if scale and scale != 1.0:
                nw = max(1, int(logo_layer.width * scale))
                nh = max(1, int(logo_layer.height * scale))
                logo_layer = logo_layer.resize((nw, nh), Image.LANCZOS)
            x_pct = float(settings.get("logo_x_pct", 0.5))
            y_pct = float(settings.get("logo_y_pct", 0.82))
            rotation = float(settings.get("logo_rotation", 0.0))
            if rotation:
                logo_layer = logo_layer.rotate(rotation, expand=True, resample=Image.BICUBIC)
            _paste_centered(canvas, logo_layer, int(base_w * x_pct), int(base_h * y_pct))

    return canvas


def apply_bg_filter(img: Image.Image, mode: str, intensity: float) -> Image.Image:
    mode = (mode or "none").lower()
    base = img.convert("RGBA")
    intensity = max(0.0, min(1.0, float(intensity)))
    # Empuja un poco mas el efecto
    strength = min(1.0, intensity * 1.4)
    if mode == "sepia":
        gray = ImageOps.grayscale(base).convert("L")
        sepia = ImageOps.colorize(gray, "#5B3A1E", "#F6D6B5").convert("RGBA")
        return Image.blend(base, sepia, strength)
    if mode == "bw":
        gray = ImageOps.grayscale(base).convert("RGBA")
        return Image.blend(base, gray, strength)
    if mode == "cool":
        r, g, b, a = base.split()
        r = ImageEnhance.Brightness(r).enhance(1.0 - 0.25 * strength)
        b = ImageEnhance.Brightness(b).enhance(1.0 + 0.45 * strength)
        merged = Image.merge("RGBA", (r, g, b, a))
        return Image.blend(base, merged, strength)
    if mode == "warm":
        r, g, b, a = base.split()
        r = ImageEnhance.Brightness(r).enhance(1.0 + 0.45 * strength)
        b = ImageEnhance.Brightness(b).enhance(1.0 - 0.25 * strength)
        merged = Image.merge("RGBA", (r, g, b, a))
        return Image.blend(base, merged, strength)
    return base
