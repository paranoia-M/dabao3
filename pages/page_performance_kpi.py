# pages/page_performance_kpi.py
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGroupBox, QCheckBox, QSplitter, QMessageBox, 
                             QGraphicsPolygonItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPolygonF, QPainter # 导入 QPainter
import pyqtgraph as pg

# --- 核心修正点 1: 彻底重写 RadarChartItem ---
class RadarChartItem(pg.GraphicsObject):
    def __init__(self, data, ranges, pen, brush=None):
        super().__init__()
        self.data = data
        self.ranges = ranges
        self.pen = pen
        self.brush = brush
        # 我们不再预先生成 QPicture

    def boundingRect(self):
        # 返回一个足够大的固定边界框
        return pg.QtCore.QRectF(-125, -125, 250, 250)

    def paint(self, painter, option, widget=None):
        """直接在 paint 方法中进行绘制"""
        painter.setRenderHint(QPainter.Antialiasing) # 开启抗锯齿
        
        num_vars = len(self.data)
        if num_vars == 0: return
        
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False) + np.pi / 2
        scaled_data = []
        for i in range(num_vars):
            r_min, r_max = self.ranges[i]; val = self.data[i]
            if r_min > r_max: scaled_data.append((r_min - val) / (r_min - r_max))
            else: scaled_data.append((val - r_min) / (r_max - r_min))
        
        points = [pg.QtCore.QPointF(np.clip(s, 0, 1) * 100 * np.cos(a), 
                                    np.clip(s, 0, 1) * 100 * np.sin(a)) for s, a in zip(scaled_data, angles)]
        
        polygon = QPolygonF(points)
        
        if self.brush:
            painter.setBrush(self.brush)
            painter.setPen(pg.mkPen(None))
            painter.drawPolygon(polygon)
            
        painter.setPen(self.pen)
        painter.setBrush(pg.mkBrush(None))
        # 绘制封闭的多边形边框
        painter.drawPolygon(polygon)


class PagePerformanceKpi(QWidget):
    def __init__(self):
        super().__init__()
        self._load_mock_data()
        
        main_layout = QHBoxLayout(self)
        left_panel = self._create_radar_panel()
        right_panel = self._create_trend_panel()
        main_layout.addWidget(left_panel, 1); main_layout.addWidget(right_panel, 2)

    def _create_radar_panel(self):
        panel = QGroupBox("KPI 综合绩效雷达图"); layout = QVBoxLayout(panel)
        self.radar_plot = pg.PlotWidget()
        self.radar_plot.setBackground(None)
        self.radar_plot.hideAxis('left'); self.radar_plot.hideAxis('bottom')
        self.radar_plot.setAspectLocked(True)
        self._draw_radar_background_and_data()
        layout.addWidget(self.radar_plot)
        return panel
        
    def _draw_radar_background_and_data(self):
        self.kpi_labels = ["计划达成率", "OEE", "合格率", "准时交付率", "单位成本"]
        self.kpi_ranges = [(80, 100), (75, 95), (98, 100), (95, 100), (0.15, 0.1)]
        num_vars = len(self.kpi_labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False) + np.pi / 2

        grid_pen = pg.mkPen(color='#BDBDBD', style=Qt.DotLine)
        for r in [25, 50, 75, 100]:
            points = [pg.QtCore.QPointF(r * np.cos(a), r * np.sin(a)) for a in angles]
            polygon_item = QGraphicsPolygonItem(QPolygonF(points + [points[0]]))
            polygon_item.setPen(grid_pen)
            self.radar_plot.addItem(polygon_item)

        for a in angles: self.radar_plot.plot([0, 100 * np.cos(a)], [0, 100 * np.sin(a)], pen=grid_pen)
        
        for i in range(num_vars):
            text = pg.TextItem(self.kpi_labels[i], anchor=(0.5, 0.5), color='#616161')
            text.setPos(125 * np.cos(angles[i]), 125 * np.sin(angles[i]))
            self.radar_plot.addItem(text)
            
        target_data = [95, 85, 99, 98, 0.12]
        actual_data = [self.kpi_data[label][-1] for label in self.kpi_labels]
        
        target_item = RadarChartItem(target_data, self.kpi_ranges, pen=pg.mkPen('#757575', style=Qt.DotLine, width=2))
        actual_item = RadarChartItem(actual_data, self.kpi_ranges, 
                                     pen=pg.mkPen('#009688', width=3), 
                                     brush=pg.mkBrush(0, 150, 136, 80))
        
        self.radar_plot.addItem(target_item); self.radar_plot.addItem(actual_item)
        
        self.radar_plot.setXRange(-140, 140); self.radar_plot.setYRange(-140, 140)

    # ... (之后的所有方法都保持不变)
    def _create_trend_panel(self):
        panel = QGroupBox("历史KPI趋势对比"); layout = QVBoxLayout(panel); controls_layout = QHBoxLayout()
        self.checkboxes = {}
        for label in self.kpi_labels:
            cb = QCheckBox(label); cb.setChecked(True); cb.stateChanged.connect(self._update_trend_chart)
            self.checkboxes[label] = cb; controls_layout.addWidget(cb)
        self.trend_plot = pg.PlotWidget(); self.trend_plot.setBackground(None); self.trend_plot.addLegend(); self.trend_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trend_plot.getAxis('left').setTextPen('black'); self.trend_plot.getAxis('bottom').setTextPen('black')
        layout.addLayout(controls_layout); layout.addWidget(self.trend_plot); self._update_trend_chart()
        return panel
        
    def _update_trend_chart(self):
        self.trend_plot.clear(); self.trend_plot.getPlotItem().legend.items = []
        colors = ['c', 'y', 'g', 'm', 'r']
        for i, (label, cb) in enumerate(self.checkboxes.items()):
            if cb.isChecked():
                data = self.kpi_data[label]; curve = self.trend_plot.plot(data, pen=colors[i], name=label)
                mean, std = np.mean(data), np.std(data); anomalies_x = np.where(data < mean - 1.5 * std)[0]
                if len(anomalies_x) > 0:
                    scatter = pg.ScatterPlotItem(x=anomalies_x, y=data[anomalies_x], symbol='o', size=15, pen='r', brush='r')
                    scatter.sigClicked.connect(self._on_anomaly_clicked); self.trend_plot.addItem(scatter)

    def _on_anomaly_clicked(self, plot, points):
        point = points[0]; day_index = int(point.pos().x()); kpi_name = ""
        for name, cb in self.checkboxes.items():
            if cb.isChecked() and len(self.kpi_data[name]) > day_index and self.kpi_data[name][day_index] == point.pos().y():
                kpi_name = name; break
        reason = self.db_root_causes.get(day_index, "未找到明确原因。")
        QMessageBox.information(self, "根本原因分析", f"日期: Day {-30 + day_index}\nKPI: {kpi_name} ({point.pos().y():.2f})\n\n<b>可能原因:</b>\n{reason}")

    def _load_mock_data(self):
        days = 30; self.kpi_data = { "计划达成率": 96 + np.random.randn(days) * 2, "OEE": 88 + np.random.randn(days) * 3, "合格率": 99.5 + np.random.randn(days) * 0.2,
                                     "准时交付率": 98 + np.random.randn(days), "单位成本": 0.13 + np.random.randn(days) * 0.01 }
        self.kpi_data["OEE"][15] = 72.5; self.kpi_data["合格率"][22] = 97.1
        self.db_root_causes = { 15: "挤出机A发生3次'压力过载'报警...", 22: "批次为 MAT-PP-B91 的原料存在杂质问题。" }