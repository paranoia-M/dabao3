# pages/widgets/mes_widgets.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF

# --- 核心修正点 1: 确保 PacingGauge 类被正确定义 ---
class PacingGauge(QWidget):
    """一个用于显示节拍/周期对比的仪表盘控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 150)
        self.value = 0.5 # 0-1, 0.5 is target
        self.takt_time = 10.0 # seconds

    def set_value(self, cycle_time):
        if cycle_time <= 0: self.value = 0.5
        else: self.value = self.takt_time / cycle_time / 2
        self.value = min(1, max(0, self.value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 1.2)
        painter.scale(side / 250.0, side / 250.0)
        
        painter.save()
        pen = QPen(); pen.setWidth(20)
        
        pen.setColor(QColor("#D32F2F")); painter.setPen(pen)
        painter.drawArc(-100, -100, 200, 200, 0 * 16, -60 * 16) # Red
        
        pen.setColor(QColor("#FFC107")); painter.setPen(pen)
        painter.drawArc(-100, -100, 200, 200, -60 * 16, -60 * 16) # Yellow

        pen.setColor(QColor("#4CAF50")); painter.setPen(pen)
        painter.drawArc(-100, -100, 200, 200, -120 * 16, -60 * 16) # Green
        painter.restore()
        
        painter.save()
        pen = QPen(Qt.white, 4); painter.setPen(pen)
        painter.setBrush(Qt.white)
        
        # --- 核心修正点 2: 使用 PyQt5 原生的 QPolygonF 和 QPointF ---
        needle = QPolygonF([QPointF(0, 0), QPointF(-5, -80), QPointF(5, -80)])
        
        angle = -180 * self.value
        painter.rotate(angle)
        painter.drawPolygon(needle)
        painter.restore()
        
        painter.setBrush(QColor("#37474F"))
        painter.drawEllipse(-15, -15, 30, 30)