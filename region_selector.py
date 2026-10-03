import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor

class RegionSelector(QWidget):
    region_selected = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        self.begin_pos = QPoint()
        self.end_pos = QPoint()
        self.is_selecting = False

        # Cover virtual desktop (all screens)
        desktop_rect = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(desktop_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.begin_pos = event.pos()
            self.end_pos = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            selected_rect = QRect(self.begin_pos, self.end_pos).normalized()
            if selected_rect.width() > 10 and selected_rect.height() > 10:
                self.region_selected.emit(selected_rect)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self.is_selecting:
            rect = QRect(self.begin_pos, self.end_pos).normalized()

            # Clear selected rectangle area to show clear screen underneath
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw vibrant glowing selection border
            pen = QPen(QColor(0, 255, 150), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Draw size indicator text above selection
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            text = f" {rect.width()} x {rect.height()} px "
            text_rect = QRect(rect.left(), max(0, rect.top() - 25), 140, 22)
            
            painter.fillRect(text_rect, QColor(0, 0, 0, 200))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        else:
            # Instruction banner at screen center
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255)))
            banner_rect = QRect(self.width() // 2 - 250, 40, 500, 50)
            painter.fillRect(banner_rect, QColor(20, 20, 30, 220))
            painter.drawRect(banner_rect)
            painter.drawText(banner_rect, Qt.AlignmentFlag.AlignCenter, "Klik & Tarik Area Subtitle Game (ESC untuk batal)")
