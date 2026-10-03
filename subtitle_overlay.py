import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRectF, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics

class SubtitleLabel(QLabel):
    """Custom QLabel with crisp 360-degree text stroke outline and word wrap"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.outline_color = QColor(0, 0, 0)
        self.text_color = QColor(255, 215, 0) # Subtitle Gold
        self.font_size = 24
        self.outline_width = 4
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_font_size(self, size):
        self.font_size = size
        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        self.setFont(font)
        self.update()

    def set_colors(self, text_hex, outline_hex="#000000", outline_width=4):
        self.text_color = QColor(text_hex)
        self.outline_color = QColor(outline_hex)
        self.outline_width = outline_width
        self.update()

    def calculate_needed_height(self, target_width):
        if not self.text():
            return 0

        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        
        flags = int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)
        avail_width = max(100, target_width - 30)
        rect = fm.boundingRect(QRect(0, 0, avail_width, 10000), flags, self.text())
        
        needed_h = rect.height() + self.outline_width * 2 + 16
        return max(10, needed_h)

    def paintEvent(self, event):
        if not self.text():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)

        rect = QRectF(self.rect())
        flags = int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)

        pen_outline = QPen(self.outline_color, self.outline_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen_outline)
        
        w = max(1, self.outline_width // 2)
        for dx in range(-w, w + 1):
            for dy in range(-w, w + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(rect.adjusted(dx, dy, dx, dy), flags, self.text())

        # Main text fill
        painter.setPen(QPen(self.text_color))
        painter.drawText(rect, flags, self.text())


class SubtitleOverlay(QWidget):
    position_changed = pyqtSignal(dict)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.old_pos = QPoint()
        self.is_moving = False
        self.is_locked = False

        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header Bar (for dragging & locking)
        self.header_bar = QWidget(self)
        self.header_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 30, 220);
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QLabel {
                color: #CCCCCC;
                font-size: 11px;
                font-family: 'Segoe UI';
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                color: #00E676;
                border: 1px solid #00E676;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 230, 118, 40);
            }
        """)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(8, 3, 6, 3)

        self.title_lbl = QLabel("💬 Subtitle (Geser posisi di sini)")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        self.lock_btn = QPushButton("🔒 Kunci Posisi")
        self.lock_btn.setToolTip("Kunci posisi agar tidak sengaja tergeser saat main game")
        self.lock_btn.clicked.connect(self.toggle_lock)
        header_layout.addWidget(self.lock_btn)

        self.main_layout.addWidget(self.header_bar)

        # Subtitle Container Box
        self.subtitle_box = QWidget(self)
        box_layout = QVBoxLayout(self.subtitle_box)
        box_layout.setContentsMargins(10, 6, 10, 6)

        self.label = SubtitleLabel(self.subtitle_box)
        self.label.set_font_size(self.cfg.get("font_size", 24))
        self.label.set_colors(
            self.cfg.get("text_color", "#FFD700"),
            self.cfg.get("outline_color", "#000000"),
            self.cfg.get("outline_width", 4)
        )
        self.label.setText("")

        box_layout.addWidget(self.label)
        self.main_layout.addWidget(self.subtitle_box)

        # Apply background style
        self.update_style()

        # Restore saved position
        pos = self.cfg.get("overlay_position", {"x": 300, "y": 700, "width": 800, "height": 120})
        self.setGeometry(pos["x"], pos["y"], pos["width"], pos["height"])

    def update_style(self):
        bg_mode = self.cfg.get("bg_mode", "none")
        opacity = self.cfg.get("bg_opacity", 0)

        if bg_mode == "none" or opacity == 0:
            bg_css = "background: transparent; border: none;"
        elif bg_mode == "dim":
            bg_css = "background-color: rgba(0, 0, 0, 120); border-radius: 6px;"
        elif bg_mode == "dark":
            bg_css = "background-color: rgba(0, 0, 0, 210); border-radius: 6px;"
        else:
            bg_css = f"background-color: rgba(0, 0, 0, {opacity}); border-radius: 6px;"

        self.subtitle_box.setStyleSheet(f"QWidget {{ {bg_css} }}")

    def auto_adjust_height(self):
        """Dynamically adjusts overlay height downwards to fit long text without cutting off lines"""
        needed_label_h = self.label.calculate_needed_height(self.width())
        header_h = self.header_bar.height() if self.header_bar.isVisible() else 0
        total_needed_h = needed_label_h + header_h + (12 if needed_label_h > 0 else 0)

        if abs(self.height() - total_needed_h) > 5:
            self.resize(self.width(), total_needed_h)

    def set_translated_text(self, text):
        self.label.setText(text if text else "")
        self.auto_adjust_height()

    def set_font_size(self, size):
        self.cfg["font_size"] = size
        self.label.set_font_size(size)
        self.auto_adjust_height()

    def set_text_color(self, hex_color):
        self.cfg["text_color"] = hex_color
        self.label.set_colors(
            hex_color,
            self.cfg.get("outline_color", "#000000"),
            self.cfg.get("outline_width", 4)
        )
        self.auto_adjust_height()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.setText("🔓 Buka Kunci")
            self.title_lbl.setText("💬 Subtitle (Terkunci)")
            
            if self.cfg.get("hide_header_on_lock", True):
                self.header_bar.hide()
        else:
            self.lock_btn.setText("🔒 Kunci Posisi")
            self.title_lbl.setText("💬 Subtitle (Geser posisi di sini)")
            self.header_bar.show()

        self.auto_adjust_height()

    def set_header_visible(self, visible):
        if visible and not self.is_locked:
            self.header_bar.show()
        elif not visible:
            self.header_bar.hide()
        self.auto_adjust_height()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # Mouse Dragging functionality for frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            self.is_moving = True
            self.old_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_moving and not self.is_locked:
            new_pos = event.globalPosition().toPoint() - self.old_pos
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_moving:
            self.is_moving = False
            geo = self.geometry()
            pos_dict = {"x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()}
            self.position_changed.emit(pos_dict)
