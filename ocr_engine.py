import time
import asyncio
import requests
import numpy as np
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal, QRect, QObject
from PyQt6.QtGui import QGuiApplication

import winocr
from rapidocr_onnxruntime import RapidOCR

class TranslationWorker(QThread):
    translation_done = pyqtSignal(str, str) # (original, translated)
    status_updated = pyqtSignal(str)         # status text
    error_occurred = pyqtSignal(str)         # error message

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.is_running = False
        self.last_clean_text = ""

        try:
            self.rapid_engine = RapidOCR()
        except Exception as e:
            self.rapid_engine = None
            print(f"RapidOCR Init Warning: {e}")

    def update_config(self, cfg):
        self.cfg = cfg

    def clear_cache(self):
        self.last_clean_text = ""

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
                    # Auto Subtitle Zone (Bottom 30% Center of screen where 99% game subtitles sit)
                    sw, sh = screen.geometry().width(), screen.geometry().height()
                    x = int(sw * 0.15)
                    y = int(sh * 0.68)
                    w = int(sw * 0.70)
                    h = int(sh * 0.28)
                    pixmap = screen.grabWindow(0, x, y, w, h)
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

                # Perform OCR
                if cap_mode in ["auto_full", "auto_bottom"]:
                    ocr_text = self.perform_full_screen_dialogue_ocr(pil_img)
                else:
                    ocr_text = self.perform_ocr(pil_img)

                if not self.is_running:
                    break

                clean_text = self.clean_text(ocr_text)

                # Smart Cache Check
                if clean_text and clean_text != self.last_clean_text:
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

    def perform_ocr(self, pil_img):
        engine = self.cfg.get("ocr_engine", "winocr")
        src_lang = self.cfg.get("source_lang", "auto")

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
                    res = await winocr.recognize_pil(pil_img, lang=win_lang)
                    return res.text if res else ""
                return asyncio.run(run_winocr())
            except Exception as e:
                print(f"WinOCR error, fallback to RapidOCR: {e}")
                engine = "rapidocr"

        if engine == "rapidocr" and self.rapid_engine:
            try:
                img_np = np.array(pil_img)
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
        return text

    def translate_text(self, text, source_lang):
        """Translates text to Indonesian using GTX Google endpoint"""
        try:
            sl = source_lang if source_lang != "auto" else "auto"
            params = {
                "client": "gtx",
                "sl": sl,
                "tl": "id",
                "dt": "t",
                "q": text
            }
            resp = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params=params,
                timeout=4.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and data[0]:
                    translated_chunks = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
                    return " ".join(translated_chunks)
        except Exception as e:
            print(f"Translation HTTP error: {e}")
        return f"[Gagal menterjemahkan]: {text}"

    def stop(self):
        self.clear_cache()
        self.is_running = False
