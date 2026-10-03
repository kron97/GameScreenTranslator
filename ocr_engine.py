import time
import asyncio
import requests
import difflib
import numpy as np
from PIL import Image, ImageEnhance
from PyQt6.QtCore import QThread, pyqtSignal, QRect, QObject
from PyQt6.QtGui import QGuiApplication

import winocr
from rapidocr_onnxruntime import RapidOCR
from translation_cache import TranslationCache

def get_active_game_window_rect():
    """Detects physical bounding rect (x, y, w, h) of active game window if focused."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd or hwnd == 0:
            return None

        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            ignore = ["GAMETRANSLATOR", "SUBTITLE", "EXPLORER", "PROGRAM MANAGER", "TASKBAR", "SETTINGS", "CMD.EXE"]
            if any(ig in title.upper() for ig in ignore):
                return None

        rect = ctypes.wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            gx, gy = max(0, rect.left), max(0, rect.top)
            gw = rect.right - rect.left
            gh = rect.bottom - rect.top
            if gw > 300 and gh > 200:
                return (gx, gy, gw, gh)
    except Exception:
        pass
    return None


def compute_image_dhash(pil_img):
    """Computes a 64-bit difference hash (dhash) for 0ms visual frame diffing."""
    try:
        img = pil_img.convert("L").resize((9, 8), Image.Resampling.NEAREST)
        pixels = list(img.getdata())
        diff = []
        for row in range(8):
            for col in range(8):
                pixel_left = pixels[row * 9 + col]
                pixel_right = pixels[row * 9 + col + 1]
                diff.append(pixel_left > pixel_right)
        decimal_val = 0
        for bit in diff:
            decimal_val = (decimal_val << 1) | bit
        return decimal_val
    except Exception:
        return None


class TranslationWorker(QThread):
    translation_done = pyqtSignal(str, str) # (original, translated)
    status_updated = pyqtSignal(str)         # status text
    error_occurred = pyqtSignal(str)         # error message

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.is_running = False
        self.last_clean_text = ""
        self.last_img_hash = None
        self.cache = TranslationCache()

        # Persistent HTTP Session for connection pooling (0ms TLS handshake overhead)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            self.rapid_engine = RapidOCR()
        except Exception as e:
            self.rapid_engine = None
            print(f"RapidOCR Init Warning: {e}")

    def update_config(self, cfg):
        self.cfg = cfg
        self.clear_cache()

    def clear_cache(self):
        self.last_clean_text = ""
        self.last_img_hash = None

    def run(self):
        self.is_running = True
        self.clear_cache()
        self.status_updated.emit("Aktif - Memindai layar...")

        while self.is_running:
            try:
                if not self.is_running:
                    break

                cap_mode = self.cfg.get("capture_mode", "selected_region")
                screen = QGuiApplication.primaryScreen()
                if not screen or not self.is_running:
                    time.sleep(0.1)
                    continue

                if cap_mode == "auto_bottom":
                    full_pix = screen.grabWindow(0)
                    if not full_pix or full_pix.isNull():
                        time.sleep(0.1)
                        continue
                    pw, ph = full_pix.width(), full_pix.height()

                    # Game Window Lock: Check if active game window is detected
                    game_rect = get_active_game_window_rect()
                    if game_rect:
                        gx, gy, gw, gh = game_rect
                        x = max(0, gx + int(gw * 0.08))
                        y = max(0, gy + int(gh * 0.68))
                        w = min(pw - x, int(gw * 0.84))
                        h = min(ph - y, int(gh * 0.29))
                    else:
                        x = int(pw * 0.08)
                        y = int(ph * 0.68)
                        w = int(pw * 0.84)
                        h = int(ph * 0.29)

                    pixmap = full_pix.copy(x, y, w, h)
                elif cap_mode == "auto_full":
                    pixmap = screen.grabWindow(0)
                else:
                    # Selected region
                    region = self.cfg.get("region", {})
                    x = region.get("x", 100)
                    y = region.get("y", 100)
                    w = region.get("width", 800)
                    h = region.get("height", 150)

                    if w <= 10 or h <= 10:
                        time.sleep(0.2)
                        continue

                    pixmap = screen.grabWindow(0, x, y, w, h)

                if pixmap.isNull() or not self.is_running:
                    time.sleep(0.1)
                    continue

                # Convert QPixmap / QImage to PIL Image
                qimg = pixmap.toImage()
                qimg = qimg.convertToFormat(qimg.Format.Format_RGB888)

                width = qimg.width()
                height = qimg.height()
                ptr = qimg.bits()
                ptr.setsize(height * width * 3)

                pil_img = Image.frombuffer("RGB", (width, height), ptr, "raw", "RGB", 0, 1)

                if not self.is_running:
                    break

                # 0ms Visual Diff Check: Skip OCR if subtitle area pixels haven't changed
                img_hash = compute_image_dhash(pil_img)
                if img_hash is not None and self.last_img_hash is not None:
                    diff_bits = bin(img_hash ^ self.last_img_hash).count("1")
                    if diff_bits <= 4:  # Tolerant threshold for camera panning/background motion
                        time.sleep(0.08)
                        continue
                self.last_img_hash = img_hash

                # Perform OCR
                if cap_mode in ["auto_full", "auto_bottom"]:
                    ocr_text = self.perform_full_screen_dialogue_ocr(pil_img)
                else:
                    ocr_text = self.perform_ocr(pil_img)

                if not self.is_running:
                    break

                clean_text = self.clean_text(ocr_text)

                # Smart Fuzzy Cache Check: Prevents translation flickering on 3D background movement
                if clean_text:
                    if self.last_clean_text:
                        # Compare similarity ratio with active subtitle line
                        similarity = difflib.SequenceMatcher(None, clean_text.lower(), self.last_clean_text.lower()).ratio()
                        if similarity >= 0.85:
                            # Subtitle text is essentially identical (>= 85% match), skip re-translation to avoid flicker
                            continue

                    self.last_clean_text = clean_text
                    
                    translated = self.translate_text(clean_text, self.cfg.get("source_lang", "auto"))
                    if self.is_running:
                        self.translation_done.emit(clean_text, translated)
                elif not clean_text:
                    if self.last_clean_text != "":
                        self.last_clean_text = ""
                        if self.is_running:
                            self.translation_done.emit("", "")

            except Exception as e:
                print(f"OCR Worker Loop Exception: {e}")

            interval = max(0.3, self.cfg.get("interval", 0.8))
            end_time = time.time() + interval
            while self.is_running and time.time() < end_time:
                time.sleep(0.04)

        try:
            self.status_updated.emit("Diberhentikan")
        except Exception:
            pass

    def is_likely_dialogue(self, text, y_center=None, img_height=720):
        text = text.strip()
        if len(text) < 3:
            return False
        # Ignore pure numbers or menu words like RESUME, SAVE GAME, etc
        ignore_words = ["RESUME", "SAVE GAME", "LOAD GAME", "SETTINGS", "TUTORIALS", "GWENT DECK", "QUIT TO MAIN MENU", "EXIT", "SNIPPING TOOL"]
        if any(w in text.upper() for w in ignore_words):
            return False
        if text.replace("/", "").replace(":", "").replace(".", "").replace(" ", "").isdigit():
            return False
        has_text_char = any(c.isalpha() or ord(c) > 0x2E80 for c in text)
        if not has_text_char:
            return False
        return True

    def perform_full_screen_dialogue_ocr(self, pil_img):
        """Full screen / zone OCR with dialogue heuristic filtering"""
        engine = self.cfg.get("ocr_engine", "winocr")
        
        if engine == "rapidocr" or not winocr:
            if self.rapid_engine:
                try:
                    img_np = np.array(pil_img)
                    res, _ = self.rapid_engine(img_np)
                    if res:
                        dialogue_lines = []
                        h = pil_img.height
                        for line in res:
                            bbox_pts, text, score = line[0], line[1], line[2]
                            ys = [p[1] for p in bbox_pts]
                            y_center = (min(ys) + max(ys)) / 2
                            if self.is_likely_dialogue(text, y_center, h):
                                dialogue_lines.append(text)
                        return " ".join(dialogue_lines)
                except Exception as e:
                    print(f"RapidOCR full screen error: {e}")

        return self.perform_ocr(pil_img)

    def preprocess_image_for_ocr(self, pil_img):
        """Preprocesses cropped subtitle image by upscaling 2x and enhancing contrast for maximum OCR precision."""
        try:
            w, h = pil_img.size
            if w < 20 or h < 10:
                return pil_img
            # Upscale 2x for sharp letter edge recognition
            scaled = pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
            enhancer = ImageEnhance.Contrast(scaled)
            return enhancer.enhance(1.4)
        except Exception:
            return pil_img

    def perform_ocr(self, pil_img):
        engine = self.cfg.get("ocr_engine", "winocr")
        src_lang = self.cfg.get("source_lang", "auto")

        # Apply 2x upscale + contrast enhancement for stylized game fonts
        proc_img = self.preprocess_image_for_ocr(pil_img)

        lang_map_win = {
            "en": "en",
            "ja": "ja",
            "zh-CN": "zh-Hans",
            "ko": "ko",
            "auto": "en"
        }

        if engine == "winocr":
            try:
                win_lang = lang_map_win.get(src_lang, "en")
                async def run_winocr():
                    res = await winocr.recognize_pil(proc_img, lang=win_lang)
                    return res.text if res else ""
                return asyncio.run(run_winocr())
            except Exception as e:
                print(f"WinOCR error, fallback to RapidOCR: {e}")
                engine = "rapidocr"

        if engine == "rapidocr" and self.rapid_engine:
            try:
                img_np = np.array(proc_img)
                res, _ = self.rapid_engine(img_np)
                if res:
                    lines = [line[1] for line in res]
                    return " ".join(lines)
            except Exception as e:
                print(f"RapidOCR error: {e}")

        return ""

    def clean_text(self, text):
        if not text:
            return ""
        text = " ".join(text.split())
        if len(text) < 2:
            return ""
        
        # Self-UI Exclusion Filter: Never translate GameTranslator ID's own window UI text
        app_ui_keywords = [
            "BAHASA ASAL", "MESIN OCR", "MESIN PENERJEMAH", "GOOGLE GTX", "DEEPL",
            "PASTE DEEPL", "SEMBUNYIKAN BILAH JUDUL", "PILIH AREA SUBTITLE", "TENTANG APLIKASI",
            "MODUS TANGKAPAN", "KONTROL UTAMA"
        ]
        text_upper = text.upper()
        if any(kw in text_upper for kw in app_ui_keywords):
            return ""

        # Filter out garbage noise lines consisting of non-word special characters (e.g. "•-*5SX-e•")
        alpha_count = sum(1 for c in text if c.isalpha() or ord(c) > 0x2E80)
        if alpha_count < 3 and len(text) > 4:
            return ""

        # Remove weird non-ASCII symbols like € or \ inside words
        text = text.replace("€", "").replace("•", "").replace("chxe", "the")

        # Common OCR fixes for serif game fonts
        text = text.replace("•\\dea", "idea").replace("•dea", "idea").replace("Gooå", "Good")
        text = text.replace("shou\\d", "should").replace("iotches", "notches")
            
        return text.strip()

    def translate_text(self, text, source_lang):
        """Hybrid Translation Pipeline:
           1. Local SQLite Cache Lookup (0ms instant response & quota saving)
           2. Qwen 2.5 3B Local LLM (Offline AI dialogue translation)
           3. DeepL Free/Pro API (High quality natural translation)
           4. Google GTX API (Free Fallback)
        """
        if not text:
            return ""

        # Step 1: Check Local SQLite Cache (0ms response)
        try:
            cached = self.cache.lookup(text)
            if cached:
                return cached
        except Exception as e:
            print(f"Cache Lookup Error: {e}")

        # Step 2: Determine Configured Translator Engine
        engine_choice = self.cfg.get("translator_engine", "google")
        deepl_key = self.cfg.get("deepl_api_key", "").strip()
        translated = None

        # Local Qwen 2.5 3B LLM Engine
        if engine_choice == "qwen":
            translated = self.translate_qwen(text, source_lang)
            if translated:
                self.cache.store(text, translated, "qwen2.5:3b")
                return translated

        # DeepL API Engine
        if engine_choice == "deepl" and deepl_key:
            translated = self.translate_deepl(text, source_lang, deepl_key)
            if translated:
                self.cache.store(text, translated, "deepl")
                return translated

        # Google GTX Fallback Engine
        translated = self.translate_google(text, source_lang)
        if translated and not translated.startswith("[Gagal"):
            self.cache.store(text, translated, "google")
            return translated

        return translated or f"[Gagal menterjemahkan]: {text}"

    def translate_qwen(self, text, source_lang):
        """Translates text using local Qwen 2.5 3B model running on Ollama / Local LLM server"""
        url = self.cfg.get("qwen_url", "http://localhost:11434/api/generate").strip()
        model_name = self.cfg.get("qwen_model", "qwen2.5:3b").strip()
        
        payload = {
            "model": model_name,
            "system": "You are a professional game subtitle translator. Translate the given text accurately into natural, fluent Indonesian for video game dialogue. Output ONLY the translated Indonesian text with no quotes, no preamble, and no extra notes.",
            "prompt": text,
            "stream": False,
            "options": {
                "num_predict": 80,
                "temperature": 0.1
            }
        }
        try:
            resp = self.session.post(url, json=payload, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                res_text = data.get("response", "").strip()
                if res_text:
                    if res_text.startswith('"') and res_text.endswith('"'):
                        res_text = res_text[1:-1].strip()
                    return res_text
            else:
                print(f"Qwen Local LLM HTTP Error: {resp.status_code}")
        except Exception as e:
            print(f"Qwen Local LLM Request Exception: {e}")
        return None

    def translate_deepl(self, text, source_lang, api_key):
        """Translates text using DeepL Free/Pro REST API"""
        if not api_key:
            return None
        
        url = "https://api-free.deepl.com/v2/translate" if api_key.endswith(":fx") else "https://api.deepl.com/v2/translate"
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        target_lang = "ID"
        sl = source_lang.upper() if (source_lang and source_lang != "auto") else "EN"
        
        payload = {
            "text": [text],
            "target_lang": target_lang,
            "source_lang": sl
        }

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=2.5)
            if resp.status_code == 200:
                data = resp.json()
                if data and "translations" in data and len(data["translations"]) > 0:
                    return data["translations"][0]["text"]
            else:
                print(f"DeepL API HTTP Error Status: {resp.status_code}")
        except Exception as e:
            print(f"DeepL API Request Exception: {e}")
        return None

    def translate_google(self, text, source_lang):
        """Translates text to Indonesian using GTX Google endpoint with persistent HTTP session"""
        try:
            # Explicitly force English if auto to avoid Google GTX switching to French/Spanish on short words
            sl = source_lang if (source_lang and source_lang != "auto") else "en"
            params = {
                "client": "gtx",
                "sl": sl,
                "tl": "id",
                "dt": "t",
                "q": text
            }
            resp = self.session.get(
                "https://translate.googleapis.com/translate_a/single",
                params=params,
                timeout=2.5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and data[0]:
                    translated_chunks = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
                    return " ".join(translated_chunks)
        except Exception as e:
            print(f"Google GTX HTTP error: {e}")
        return None

    def stop(self):
        self.clear_cache()
        self.is_running = False
