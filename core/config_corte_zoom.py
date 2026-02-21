DEFAULTS = {
    "crop_top_pct": 25.0,
    "crop_bottom_pct": 25.0,
    "crop_left_pct": 50.0,
    "crop_right_pct": 0.0,
    "zoom_factor": 1.2,
    "bg_enabled": False,
    "cinta_enabled": False,
    "cinta_left_pct": 20.0,
    "cinta_top_pct": 75.0,
    "cinta_width_pct": 42.0,
    "cinta_height_pct": 10.0,
    "cinta_bg_color": "#000000",
    "cinta_border_color": "#F8BA11",
    "cinta_text_color": "#FFFFFF",
    "cinta_nombre": "Roberto Ramírez Basterrechea",
    "cinta_rol": "Host / @gobernanzaciudadanadigital",
    "cinta_text_scale": 1.0,
    "cinta_name_scale": 0.35,
    "cinta_role_scale": 0.2,
    "cinta_fontfile_name": "C:\\Windows\\Fonts\\arialbd.ttf",
    "cinta_fontfile_role": "C:\\Windows\\Fonts\\arial.ttf",
}


def get_corte_zoom_defaults() -> dict:
    return dict(DEFAULTS)
