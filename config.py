import json
import os

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "capture_mode": "selected_region", # 'selected_region', 'auto_bottom', or 'auto_full'
    "region": {"x": 100, "y": 100, "width": 800, "height": 150},
    "source_lang": "auto",
    "target_lang": "id",
    "ocr_engine": "winocr",  # 'winocr' or 'rapidocr'
    "interval": 1.0,         # seconds
    "font_size": 24,
    "text_color": "#FFD700",  # Gold / Subtitle Yellow
    "bg_mode": "none",       # 'none' (Hanya Teks), 'dim', 'dark', 'custom'
    "bg_opacity": 0,         # 0 = 100% transparan (tanpa kotak), 255 = pekat
    "outline_color": "#000000",
    "outline_width": 4,
    "hide_header_on_lock": True,
    "click_through": False,
    "always_on_top": True,
    "overlay_position": {"x": 300, "y": 700, "width": 800, "height": 120}
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(data)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Gagal menyimpan konfig: {e}")
