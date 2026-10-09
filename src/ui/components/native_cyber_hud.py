"""
OptiCleaner v4.0 - Native Cyber HUD Component
Custom lightweight QPainter gauge widget replacing heavy WebEngine bloat with pure native Qt graphics.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import math


class CyberGauge(QtWidgets.QWidget):
    """Draws an animated circular neon gauge with glow and percentage readouts."""

    def __init__(self, title: str = "CPU", unit: str = "%", accent_color: str = "#00E5FF", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.accent_color = QtGui.QColor(accent_color)
        self.value = 0.0
        self.setMinimumSize(140, 140)

    def set_value(self, val: float):
        self.value = max(0.0, min(100.0, float(val)))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        rect = QtCore.QRectF((width - side) / 2 + 10, (height - side) / 2 + 10, side - 20, side - 20)

        # Background track arc
        pen_bg = QtGui.QPen(QtGui.QColor("#1E293B"), 8, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, -45 * 16, -270 * 16)

        # Active progress arc
        pen_fg = QtGui.QPen(self.accent_color, 8, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
        painter.setPen(pen_fg)
        span_angle = -int((self.value / 100.0) * 270 * 16)
        painter.drawArc(rect, 225 * 16, span_angle)

        # Center Text
        painter.setPen(QtGui.QColor("#FFFFFF"))
        font_val = QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold)
        painter.setFont(font_val)
        val_str = f"{int(self.value)}{self.unit}"
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, val_str)

        # Title Text below
        painter.setPen(QtGui.QColor("#94A3B8"))
        font_title = QtGui.QFont("Segoe UI", 9, QtGui.QFont.DemiBold)
        painter.setFont(font_title)
        title_rect = QtCore.QRect(0, int(height / 2 + 22), width, 20)
        painter.drawText(title_rect, QtCore.Qt.AlignCenter, self.title)
