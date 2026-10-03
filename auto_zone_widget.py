import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QCursor, QGuiApplication

from ocr_engine import get_active_game_window_rect

class AutoZoneBoxWidget(QWidget):
    position_changed = pyqtSignal(dict)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.is_moving = False
        self.is_resizing = False
        self.resize_edge = None
        self.drag_start_pos = QPoint()
        self.drag_start_geo = QRect()
        self.is_locked = False

        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header Bar
        self.header_bar = QWidget(self)
        self.header_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(18, 30, 40, 230);
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: 1px solid #00E676;
            }
            QLabel {
                color: #00E676;
                font-size: 11px;
                font-family: 'Segoe UI';
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                color: #FFFFFF;
                border: 1px solid #00E676;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 230, 118, 50);
            }
        """)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(8, 3, 6, 3)

        self.title_lbl = QLabel("🤖 Area Subtitle Otomatis (Auto Zone)")
        header_layout.addWidget(self.title_lbl)

        self.size_lbl = QLabel("[ 0 x 0 px ]")
        self.size_lbl.setStyleSheet("color: #FFC107; margin-left: 8px;")
        header_layout.addWidget(self.size_lbl)

        header_layout.addStretch()

        self.lock_btn = QPushButton("🔒 Kunci")
        self.lock_btn.setToolTip("Kunci posisi & ukuran area ini")
        self.lock_btn.clicked.connect(self.toggle_lock)
        header_layout.addWidget(self.lock_btn)

        self.hide_btn = QPushButton("👁 Sembunyikan")
        self.hide_btn.setToolTip("Sembunyikan kotak ini (pindaian tetap berjalan)")
        self.hide_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.hide_btn)

        self.main_layout.addWidget(self.header_bar)
        self.main_layout.addStretch()

        # Restore saved position or default
        self.restore_geometry()

    def restore_geometry(self):
        region = self.cfg.get("auto_bottom_region", None)
        if region and isinstance(region, dict) and region.get("width", 0) > 20:
            self.setGeometry(region["x"], region["y"], region["width"], region["height"])
        else:
            self.reset_to_default_geometry()

        self.update_size_label()

    def reset_to_default_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen:
            desktop_rect = screen.geometry()
            pw, ph = desktop_rect.width(), desktop_rect.height()
            
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
            
            self.setGeometry(x, y, w, h)
            self.emit_position_changed()

    def update_size_label(self):
        self.size_lbl.setText(f"[ {self.width()} x {self.height()} px ]")

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.setText("🔓 Buka Kunci")
            self.title_lbl.setText("🤖 Area Subtitle (Terkunci)")
            if self.cfg.get("hide_header_on_lock", True):
                self.header_bar.hide()
        else:
            self.lock_btn.setText("🔒 Kunci")
            self.title_lbl.setText("🤖 Area Subtitle Otomatis (Auto Zone)")
            self.header_bar.show()
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 100% Transparent inside box (0% opacity fill) so game subtitles are 100% clear and un-obscured!
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Neon Cyan/Green Dashed Border
        pen_color = QColor(0, 230, 118, 60 if self.is_locked else 230)
        pen_style = Qt.PenStyle.DashLine if not self.is_locked else Qt.PenStyle.DotLine
        pen = QPen(pen_color, 2 if not self.is_locked else 1, pen_style)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # Draw Corner Resize Handle at bottom-right corner if unlocked
        if not self.is_locked:
            handle_pen = QPen(QColor(0, 230, 118), 3)
            painter.setPen(handle_pen)
            r = self.rect()
            painter.drawLine(r.right() - 12, r.bottom() - 3, r.right() - 3, r.bottom() - 12)
            painter.drawLine(r.right() - 7, r.bottom() - 3, r.right() - 3, r.bottom() - 7)

    def get_resize_edge(self, pos):
        """Determines which edge/corner mouse cursor is over"""
        if self.is_locked:
            return None

        m = 12  # margin in pixels
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()

        on_left = x <= m
        on_right = x >= w - m
        on_top = y <= m
        on_bottom = y >= h - m

        if on_bottom and on_right:
            return "bottom_right"
        elif on_bottom and on_left:
            return "bottom_left"
        elif on_top and on_right:
            return "top_right"
        elif on_top and on_left:
            return "top_left"
        elif on_left:
            return "left"
        elif on_right:
            return "right"
        elif on_top:
            return "top"
        elif on_bottom:
            return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            edge = self.get_resize_edge(event.pos())
            if edge:
                self.is_resizing = True
                self.resize_edge = edge
                self.drag_start_pos = event.globalPosition().toPoint()
                self.drag_start_geo = self.geometry()
            else:
                self.is_moving = True
                self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if not self.is_locked:
            edge = self.get_resize_edge(event.pos())
            if not self.is_resizing and not self.is_moving:
                if edge in ["bottom_right", "top_left"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeNWSECursor))
                elif edge in ["bottom_left", "top_right"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeNESWCursor))
                elif edge in ["left", "right"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
                elif edge in ["top", "bottom"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
                else:
                    self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

        if self.is_moving and not self.is_locked:
            new_pos = event.globalPosition().toPoint() - self.drag_start_pos
            self.move(new_pos)
            self.update_size_label()
            self.emit_position_changed()

        elif self.is_resizing and not self.is_locked:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            geo = QRect(self.drag_start_geo)

            if "right" in self.resize_edge:
                geo.setRight(max(geo.left() + 150, geo.right() + delta.x()))
            if "left" in self.resize_edge:
                geo.setLeft(min(geo.right() - 150, geo.left() + delta.x()))
            if "bottom" in self.resize_edge:
                geo.setBottom(max(geo.top() + 50, geo.bottom() + delta.y()))
            if "top" in self.resize_edge:
                geo.setTop(min(geo.bottom() - 50, geo.top() + delta.y()))

            self.setGeometry(geo)
            self.update_size_label()
            self.emit_position_changed()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_moving or self.is_resizing:
                self.is_moving = False
                self.is_resizing = False
                self.resize_edge = None
                self.emit_position_changed()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_size_label()

    def emit_position_changed(self):
        geo = self.geometry()
        pos_dict = {"x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()}
        self.position_changed.emit(pos_dict)
