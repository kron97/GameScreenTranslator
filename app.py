import sys
import os
import traceback
from datetime import datetime

# Ensure current directory is in python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QGroupBox, QTextEdit,
    QColorDialog, QFrame, QCheckBox, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt, QRect, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QColor

from config import load_config, save_config
from region_selector import RegionSelector
from subtitle_overlay import SubtitleOverlay
from auto_zone_widget import AutoZoneBoxWidget
from ocr_engine import TranslationWorker, log_debug

def global_excepthook(exc_type, exc_value, exc_traceback):
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_debug("FATAL EXCEPTION", f"\n{err_str}")

sys.excepthook = global_excepthook


class GameTranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.worker = None
        self.selector = None
        
        self.init_ui()

        # Initialize Subtitle Overlay Window
        self.subtitle_overlay = SubtitleOverlay(self.cfg)
        self.subtitle_overlay.position_changed.connect(self.on_overlay_moved)
        self.subtitle_overlay.show()

        # Initialize Interactive Auto Zone Box Widget
        self.auto_zone_widget = AutoZoneBoxWidget(self.cfg)
        self.auto_zone_widget.position_changed.connect(self.on_auto_zone_moved)
        if self.cfg.get("capture_mode", "selected_region") == "auto_bottom":
            self.auto_zone_widget.show()

    def init_ui(self):
        self.setWindowTitle("GameTranslator ID - Terjemahan Subtitle Game Real-Time")
        self.resize(560, 800)

        # Apply Modern Dark Theme Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121218;
            }
            QWidget {
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2D2D3D;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1A1A24;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #00E676;
            }
            QPushButton {
                background-color: #2E2E3E;
                color: #FFFFFF;
                border: 1px solid #3E3E52;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3E3E52;
                border-color: #52526E;
            }
            QPushButton:pressed {
                background-color: #1E1E2A;
            }
            QPushButton#btn_primary {
                background-color: #2196F3;
                border: none;
            }
            QPushButton#btn_primary:hover {
                background-color: #1E88E5;
            }
            QPushButton#btn_start {
                background-color: #4CAF50;
                font-size: 15px;
                padding: 10px;
                border: none;
            }
            QPushButton#btn_start:hover {
                background-color: #43A047;
            }
            QPushButton#btn_stop {
                background-color: #F44336;
                font-size: 15px;
                padding: 10px;
                border: none;
            }
            QPushButton#btn_stop:hover {
                background-color: #E53935;
            }
            QComboBox, QSpinBox {
                background-color: #222230;
                border: 1px solid #333346;
                border-radius: 4px;
                padding: 5px;
                color: #FFFFFF;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #2A2A3A;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00E676;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #161620;
                border: 1px solid #2B2B3C;
                border-radius: 6px;
                color: #00E676;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # Header Title Banner
        header = QFrame()
        header.setStyleSheet("background-color: #1E1E2C; border-radius: 8px;")
        header_layout = QVBoxLayout(header)
        
        title = QLabel("🎮 GameTranslator ID")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #00E676;")
        
        sub = QLabel("Penerjemah Subtitle Video Game ke Bahasa Indonesia (Tanpa Mod)")
        sub.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        layout.addWidget(header)

        # Section 1: Capture Mode & Region Controls
        cap_box = QGroupBox("1. Modus Tangkapan Layar (Capture Mode)")
        cap_layout = QVBoxLayout(cap_box)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Modus Deteksi:"))
        self.combo_cap_mode = QComboBox()
        self.combo_cap_mode.addItems([
            "🎯 Area Spesifik (Pilih Kotak Subtitle Manual)",
            "🤖 Auto Subtitle Zone (Otomatis Area Bawah Layar)",
            "🌐 Deteksi Otomatis Seluruh Layar"
        ])
        
        mode_map = ["selected_region", "auto_bottom", "auto_full"]
        cur_cap = self.cfg.get("capture_mode", "selected_region")
        if cur_cap in mode_map:
            self.combo_cap_mode.setCurrentIndex(mode_map.index(cur_cap))
            
        self.combo_cap_mode.currentIndexChanged.connect(self.on_capture_mode_changed)
        mode_row.addWidget(self.combo_cap_mode)
        cap_layout.addLayout(mode_row)

        self.widget_region = QWidget()
        reg_layout = QVBoxLayout(self.widget_region)
        reg_layout.setContentsMargins(0, 5, 0, 0)

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("🎯 Pilih Area Subtitle Game")
        self.btn_select.setObjectName("btn_primary")
        self.btn_select.clicked.connect(self.select_region)
        btn_layout.addWidget(self.btn_select)
        reg_layout.addLayout(btn_layout)

        reg = self.cfg.get("region", {"x": 100, "y": 100, "width": 800, "height": 150})
        self.lbl_region = QLabel(f"Area Aktif: X={reg['x']}, Y={reg['y']}, Lebar={reg['width']}px, Tinggi={reg['height']}px")
        self.lbl_region.setStyleSheet("color: #FFC107; font-size: 11px;")
        reg_layout.addWidget(self.lbl_region)

        cap_layout.addWidget(self.widget_region)
        self.widget_region.setVisible(cur_cap == "selected_region")

        # Controls for auto_bottom mode
        self.widget_auto_bottom = QWidget()
        auto_layout = QVBoxLayout(self.widget_auto_bottom)
        auto_layout.setContentsMargins(0, 5, 0, 0)

        auto_btn_layout = QHBoxLayout()
        self.btn_toggle_zone_box = QPushButton("👁 Tampilkan / Sembunyikan Kotak Area")
        self.btn_toggle_zone_box.clicked.connect(self.toggle_zone_box_visibility)
        auto_btn_layout.addWidget(self.btn_toggle_zone_box)

        self.btn_reset_zone_box = QPushButton("🔄 Reset ke Default Game/Layar")
        self.btn_reset_zone_box.clicked.connect(self.reset_zone_box)
        auto_btn_layout.addWidget(self.btn_reset_zone_box)

        auto_layout.addLayout(auto_btn_layout)

        auto_reg = self.cfg.get("auto_bottom_region", {"x": 0, "y": 0, "width": 0, "height": 0})
        self.lbl_auto_region = QLabel(f"Area Otomatis: X={auto_reg.get('x', 0)}, Y={auto_reg.get('y', 0)}, Lebar={auto_reg.get('width', 0)}px, Tinggi={auto_reg.get('height', 0)}px")
        self.lbl_auto_region.setStyleSheet("color: #00E676; font-size: 11px;")
        auto_layout.addWidget(self.lbl_auto_region)

        cap_layout.addWidget(self.widget_auto_bottom)
        self.widget_auto_bottom.setVisible(cur_cap == "auto_bottom")

        layout.addWidget(cap_box)

        # Section 2: Start / Stop Controls
        ctrl_box = QGroupBox("2. Kontrol Utama Penerjemahan")
        ctrl_layout = QVBoxLayout(ctrl_box)

        self.btn_toggle = QPushButton("▶ MULAI MENTERJEMAHKAN")
        self.btn_toggle.setObjectName("btn_start")
        self.btn_toggle.clicked.connect(self.toggle_translation)
        ctrl_layout.addWidget(self.btn_toggle)

        self.lbl_status = QLabel("Status: Siap (Klik tombol di atas untuk mulai)")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #888888; font-weight: bold;")
        ctrl_layout.addWidget(self.lbl_status)

        layout.addWidget(ctrl_box)

        # Section 3: Subtitle Appearance & Transparency Settings
        app_box = QGroupBox("3. Kustomisasi Tampilan & Transparansi Subtitle")
        app_layout = QVBoxLayout(app_box)

        bg_mode_layout = QHBoxLayout()
        bg_mode_layout.addWidget(QLabel("Model Latar Subtitle:"))
        self.combo_bg = QComboBox()
        self.combo_bg.addItems([
            "👻 Bening / Tanpa Latar (Hanya Teks Melayang)",
            "🌘 Transparan Redup (Soft Dim Box)",
            "⬛ Gelap Pekat (Dark Box)",
            "🎨 Kustom Opasitas Slider"
        ])
        
        bg_mode_map = ["none", "dim", "dark", "custom"]
        cur_mode = self.cfg.get("bg_mode", "none")
        if cur_mode in bg_mode_map:
            self.combo_bg.setCurrentIndex(bg_mode_map.index(cur_mode))

        self.combo_bg.currentIndexChanged.connect(self.on_bg_mode_changed)
        bg_mode_layout.addWidget(self.combo_bg)
        app_layout.addLayout(bg_mode_layout)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opasitas Latar (0-100%):"))
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 255)
        self.slider_opacity.setValue(self.cfg.get("bg_opacity", 0))
        self.slider_opacity.valueChanged.connect(self.on_opacity_slider_changed)
        opacity_layout.addWidget(self.slider_opacity)

        self.lbl_opacity_val = QLabel(f"{int(self.slider_opacity.value() / 2.55)}%")
        self.lbl_opacity_val.setFixedWidth(40)
        opacity_layout.addWidget(self.lbl_opacity_val)
        app_layout.addLayout(opacity_layout)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Ukuran Font:"))
        self.spin_font = QSpinBox()
        self.spin_font.setRange(14, 48)
        self.spin_font.setValue(self.cfg.get("font_size", 24))
        self.spin_font.valueChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.spin_font)

        font_layout.addWidget(QLabel("Warna Teks:"))
        self.combo_color = QComboBox()
        self.combo_color.addItems([
            "Kuning Subtitle (#FFD700)",
            "Putih Bersih (#FFFFFF)",
            "Hijau Cyan (#00E676)",
            "Kuning Cerah (#FFFF00)"
        ])
        self.combo_color.currentIndexChanged.connect(self.on_color_changed)
        font_layout.addWidget(self.combo_color)

        font_layout.addWidget(QLabel("Garis Tepi (Outline):"))
        self.spin_outline = QSpinBox()
        self.spin_outline.setRange(1, 10)
        self.spin_outline.setValue(self.cfg.get("outline_width", 4))
        self.spin_outline.valueChanged.connect(self.on_outline_changed)
        font_layout.addWidget(self.spin_outline)

        app_layout.addLayout(font_layout)

        header_opt_layout = QHBoxLayout()
        self.chk_hide_header = QCheckBox("Sembunyikan bilah judul saat posisi terkunci")
        self.chk_hide_header.setChecked(self.cfg.get("hide_header_on_lock", True))
        self.chk_hide_header.stateChanged.connect(self.on_hide_header_changed)
        header_opt_layout.addWidget(self.chk_hide_header)

        self.btn_lock_toggle = QPushButton("🔒 Kunci / Buka Posisi")
        self.btn_lock_toggle.clicked.connect(self.toggle_overlay_lock)
        header_opt_layout.addWidget(self.btn_lock_toggle)

        app_layout.addLayout(header_opt_layout)

        layout.addWidget(app_box)

        # Section 4: OCR & Language Settings
        set_box = QGroupBox("4. Pengaturan Bahasa & Mesin OCR")
        set_layout = QVBoxLayout(set_box)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Bahasa Asal:"))
        self.combo_source = QComboBox()
        self.combo_source.addItems([
            "Otomatis (Auto Detect)",
            "Inggris (English)",
            "Jepang (Japanese)",
            "Mandarin (Chinese)",
            "Korea (Korean)"
        ])
        
        lang_codes = ["auto", "en", "ja", "zh-CN", "ko"]
        cur_lang = self.cfg.get("source_lang", "auto")
        if cur_lang in lang_codes:
            self.combo_source.setCurrentIndex(lang_codes.index(cur_lang))
        self.combo_source.currentIndexChanged.connect(self.on_settings_changed)
        lang_layout.addWidget(self.combo_source)

        lang_layout.addWidget(QLabel("Tujuan:"))
        lbl_target = QLabel("🇮🇩 Bahasa Indonesia")
        lbl_target.setStyleSheet("font-weight: bold; color: #00E676;")
        lang_layout.addWidget(lbl_target)

        set_layout.addLayout(lang_layout)

        ocr_layout = QHBoxLayout()
        ocr_layout.addWidget(QLabel("Mesin OCR:"))
        self.combo_ocr = QComboBox()
        self.combo_ocr.addItems([
            "Windows Native OCR (Bawaan Windows - Cepat)",
            "RapidOCR (Offline ONNX Model)"
        ])
        if self.cfg.get("ocr_engine", "winocr") == "rapidocr":
            self.combo_ocr.setCurrentIndex(1)
        self.combo_ocr.currentIndexChanged.connect(self.on_settings_changed)
        ocr_layout.addWidget(self.combo_ocr)
        set_layout.addLayout(ocr_layout)

        trans_layout = QHBoxLayout()
        trans_layout.addWidget(QLabel("Mesin Penerjemah:"))
        self.combo_translator = QComboBox()
        self.combo_translator.addItems([
            "🧠 Qwen 2.5 3B (Local LLM Offline - Ollama)",
            "🌐 Google GTX (Gratis & Bebas Kuota)",
            "🚀 DeepL API (Terjemahan Natural + DeepL Key)"
        ])
        trans_map = ["qwen", "google", "deepl"]
        cur_trans = self.cfg.get("translator_engine", "qwen")
        if cur_trans in trans_map:
            self.combo_translator.setCurrentIndex(trans_map.index(cur_trans))
        self.combo_translator.currentIndexChanged.connect(self.on_settings_changed)
        trans_layout.addWidget(self.combo_translator)
        set_layout.addLayout(trans_layout)

        deepl_key_layout = QHBoxLayout()
        deepl_key_layout.addWidget(QLabel("DeepL API Key:"))
        self.txt_deepl_key = QLineEdit()
        self.txt_deepl_key.setPlaceholderText("Paste DeepL Free/Pro API Key (misal: 12345678-xxxx...:fx)")
        self.txt_deepl_key.setText(self.cfg.get("deepl_api_key", ""))
        self.txt_deepl_key.textChanged.connect(self.on_settings_changed)
        deepl_key_layout.addWidget(self.txt_deepl_key)
        set_layout.addLayout(deepl_key_layout)

        layout.addWidget(set_box)

        # Section 5: Live Translation Monitor Log
        mon_box = QGroupBox("5. Monitor Teks Real-Time")
        mon_layout = QVBoxLayout(mon_box)

        self.txt_monitor = QTextEdit()
        self.txt_monitor.setReadOnly(True)
        self.txt_monitor.setPlaceholderText("Teks asli dan hasil terjemahan akan tampil di sini saat game berjalan...")
        self.txt_monitor.setFixedHeight(90)
        mon_layout.addWidget(self.txt_monitor)

        layout.addWidget(mon_box)

    def on_capture_mode_changed(self, idx):
        mode_map = ["selected_region", "auto_bottom", "auto_full"]
        chosen = mode_map[idx]
        self.cfg["capture_mode"] = chosen
        self.widget_region.setVisible(chosen == "selected_region")
        self.widget_auto_bottom.setVisible(chosen == "auto_bottom")

        if chosen == "auto_bottom":
            self.auto_zone_widget.show()
        else:
            self.auto_zone_widget.hide()

        save_config(self.cfg)
        if self.worker:
            self.worker.update_config(self.cfg)

    def select_region(self):
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self.on_region_selected)
        self.selector.show()

    def on_region_selected(self, rect: QRect):
        pos_dict = {"x": rect.x(), "y": rect.y(), "width": rect.width(), "height": rect.height()}
        self.cfg["region"] = pos_dict
        save_config(self.cfg)
        self.lbl_region.setText(f"Area Aktif: X={rect.x()}, Y={rect.y()}, Lebar={rect.width()}px, Tinggi={rect.height()}px")
        
        if self.worker:
            self.worker.update_config(self.cfg)

    def toggle_translation(self):
        if self.worker and self.worker.isRunning():
            self.stop_translation()
        else:
            self.start_translation()

    def start_translation(self):
        if self.worker:
            self.stop_translation()

        log_debug("GUI ACTION", f"Mulai Menterjemahkan -> Capture Mode: '{self.cfg.get('capture_mode')}', Translator: '{self.cfg.get('translator_engine')}', OCR: '{self.cfg.get('ocr_engine')}'")
        self.worker = TranslationWorker(self.cfg)
        self.worker.translation_done.connect(self.on_translation_done)
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.start()

        self.btn_toggle.setText("⏹ HENTIKAN TERJEMAHAN")
        self.btn_toggle.setObjectName("btn_stop")
        self.btn_toggle.setStyle(self.btn_toggle.style())
        self.lbl_status.setText("Status: TERJEMAHAN ON (Memindai Subtitle...)")
        self.lbl_status.setStyleSheet("color: #00E676; font-weight: bold;")

    def stop_translation(self):
        log_debug("GUI ACTION", "Hentikan Menterjemahkan diklik pengguna")
        if self.worker:
            w = self.worker
            self.worker = None

            try:
                w.translation_done.disconnect()
                w.status_updated.disconnect()
            except Exception:
                pass

            # Connect finished signal to deleteLater so thread deletes ONLY after run() exits
            try:
                w.finished.connect(w.deleteLater)
            except Exception:
                pass

            w.stop()

        self.btn_toggle.setText("▶ MULAI MENTERJEMAHKAN")
        self.btn_toggle.setObjectName("btn_start")
        self.btn_toggle.setStyle(self.btn_toggle.style())
        self.lbl_status.setText("Status: PAUSE / OFF (Klik 'Mulai Menterjemahkan')")
        self.lbl_status.setStyleSheet("color: #888888; font-weight: bold;")
        
        # Clear text when paused
        self.subtitle_overlay.set_translated_text("")

    @pyqtSlot(str, str)
    def on_translation_done(self, orig, trans):
        if orig and trans:
            self.txt_monitor.append(f"[ASLI]: {orig}\n[INDONESIA]: {trans}\n---")
            sb = self.txt_monitor.verticalScrollBar()
            sb.setValue(sb.maximum())

        self.subtitle_overlay.set_translated_text(trans)

    @pyqtSlot(str)
    def on_status_updated(self, status):
        self.lbl_status.setText(f"Status: {status}")

    def on_bg_mode_changed(self, idx):
        mode_map = ["none", "dim", "dark", "custom"]
        chosen_mode = mode_map[idx]
        self.cfg["bg_mode"] = chosen_mode
        
        if chosen_mode == "none":
            self.cfg["bg_opacity"] = 0
            self.slider_opacity.setValue(0)
        elif chosen_mode == "dim":
            self.cfg["bg_opacity"] = 120
            self.slider_opacity.setValue(120)
        elif chosen_mode == "dark":
            self.cfg["bg_opacity"] = 210
            self.slider_opacity.setValue(210)

        self.subtitle_overlay.update_style()
        save_config(self.cfg)

    def on_opacity_slider_changed(self, val):
        self.lbl_opacity_val.setText(f"{int(val / 2.55)}%")
        self.cfg["bg_opacity"] = val
        self.cfg["bg_mode"] = "custom"
        self.subtitle_overlay.update_style()
        save_config(self.cfg)

    def on_settings_changed(self):
        lang_codes = ["auto", "en", "ja", "zh-CN", "ko"]
        self.cfg["source_lang"] = lang_codes[self.combo_source.currentIndex()]
        
        ocr_engines = ["winocr", "rapidocr"]
        self.cfg["ocr_engine"] = ocr_engines[self.combo_ocr.currentIndex()]
        
        translator_engines = ["qwen", "google", "deepl"]
        self.cfg["translator_engine"] = translator_engines[self.combo_translator.currentIndex()]
        self.cfg["deepl_api_key"] = self.txt_deepl_key.text().strip()

        save_config(self.cfg)
        if self.worker:
            self.worker.update_config(self.cfg)

    def on_font_changed(self, val):
        self.cfg["font_size"] = val
        self.subtitle_overlay.set_font_size(val)
        save_config(self.cfg)

    def on_color_changed(self, idx):
        colors = ["#FFD700", "#FFFFFF", "#00E676", "#FFFF00"]
        chosen = colors[idx]
        self.cfg["text_color"] = chosen
        self.subtitle_overlay.set_text_color(chosen)
        save_config(self.cfg)

    def on_outline_changed(self, val):
        self.cfg["outline_width"] = val
        self.subtitle_overlay.set_text_color(self.cfg.get("text_color", "#FFD700"))
        save_config(self.cfg)

    def on_hide_header_changed(self, state):
        hide = (state == Qt.CheckState.Checked.value)
        self.cfg["hide_header_on_lock"] = hide
        save_config(self.cfg)

    def toggle_overlay_lock(self):
        self.subtitle_overlay.toggle_lock()

    def on_overlay_moved(self, pos_dict):
        self.cfg["overlay_position"] = pos_dict
        save_config(self.cfg)

    def toggle_zone_box_visibility(self):
        if self.auto_zone_widget.isVisible():
            self.auto_zone_widget.hide()
        else:
            self.auto_zone_widget.show()

    def reset_zone_box(self):
        self.auto_zone_widget.reset_to_default_geometry()
        self.auto_zone_widget.show()

    def on_auto_zone_moved(self, pos_dict):
        self.cfg["auto_bottom_region"] = pos_dict
        save_config(self.cfg)
        self.lbl_auto_region.setText(f"Area Otomatis: X={pos_dict['x']}, Y={pos_dict['y']}, Lebar={pos_dict['width']}px, Tinggi={pos_dict['height']}px")
        if self.worker:
            self.worker.update_config(self.cfg)

    def closeEvent(self, event):
        self.stop_translation()
        self.subtitle_overlay.close()
        if hasattr(self, 'auto_zone_widget') and self.auto_zone_widget:
            self.auto_zone_widget.close()
        save_config(self.cfg)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameTranslatorApp()
    window.show()
    sys.exit(app.exec())
