import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QFont, QCursor

class FloatingButton(QWidget):
    toggled = pyqtSignal(bool) # True = ON (Translating), False = OFF (Paused)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.is_active = False
        self.is_moving = False
        self.old_pos = QPoint()

        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main Pill Button Container
        self.pill_btn = QPushButton("🔴 PAUSE (OFF)")
        self.pill_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.pill_btn.setToolTip("Klik untuk Mulai / Jeda Terjemahan Real-Time\n(Dapat digeser ke mana saja pada layar)")
        self.pill_btn.clicked.connect(self.on_btn_clicked)

        layout.addWidget(self.pill_btn)

        # Apply initial style
        self.update_style()

        # Restore saved position or default top-right
        pos = self.cfg.get("floating_btn_pos", {"x": 1600, "y": 80, "width": 160, "height": 38})
        self.setGeometry(pos["x"], pos["y"], pos["width"], pos["height"])

    def update_style(self):
        if self.is_active:
            self.pill_btn.setText("🟢 TRANSLATE (ON)")
            self.pill_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 200, 83, 210);
                    color: #FFFFFF;
                    border: 2px solid #00E676;
                    border-radius: 18px;
                    padding: 6px 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(0, 230, 118, 240);
                }
            """)
        else:
            self.pill_btn.setText("🔴 PAUSE (OFF)")
            self.pill_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(40, 40, 50, 190);
                    color: #CCCCCC;
                    border: 2px solid #555566;
                    border-radius: 18px;
                    padding: 6px 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(70, 70, 85, 220);
                    color: #FFFFFF;
                }
            """)

    def set_active_state(self, active: bool):
        self.is_active = active
        self.update_style()

    def on_btn_clicked(self):
        self.is_active = not self.is_active
        self.update_style()
        self.toggled.emit(self.is_active)

    # Mouse drag events
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_moving = True
            self.old_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_moving:
            new_pos = event.globalPosition().toPoint() - self.old_pos
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_moving:
            self.is_moving = False
            geo = self.geometry()
            pos_dict = {"x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()}
            self.cfg["floating_btn_pos"] = pos_dict
