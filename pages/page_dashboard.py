# pages/page_dashboard.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QGroupBox, QGraphicsRectItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import pyqtgraph as pg

from device_simulator import SchedulingSimulatorThread

class PageDashboard(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20); main_layout.setSpacing(20)
        
        left_panel = self._create_planning_panel()
        right_panel = self._create_execution_panel()
        
        main_layout.addWidget(left_panel, 1); main_layout.addWidget(right_panel, 2)

        self.time_data, self.theoretical_data, self.actual_data = [], [], []

        self.simulator = SchedulingSimulatorThread(self)
        self.simulator.data_updated.connect(self.update_ui)
        self.simulator.start()

    def _create_planning_panel(self):
        panel = QGroupBox("计划与排程 (Planning)")
        layout = QVBoxLayout(panel)
        kpi_layout = QHBoxLayout()
        self.plan_kpi = self._create_kpi_card("今日总计划", "0 米")
        self.orders_kpi = self._create_kpi_card("待处理订单", "0 个")
        kpi_layout.addWidget(self.plan_kpi); kpi_layout.addWidget(self.orders_kpi)
        
        gantt_box = QGroupBox("未来24小时甘特图预览")
        gantt_layout = QVBoxLayout(gantt_box)
        self.gantt_plot = pg.PlotWidget(); self.gantt_plot.setBackground(None)
        self.gantt_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gantt_plot.getAxis('left').setTextPen('black')
        self.gantt_plot.getAxis('bottom').setTextPen('black')
        gantt_layout.addWidget(self.gantt_plot)
        
        layout.addLayout(kpi_layout); layout.addWidget(gantt_box)
        return panel

    def _create_execution_panel(self):
        panel = QGroupBox("执行与监控 (Execution)")
        layout = QVBoxLayout(panel)
        kpi_layout = QHBoxLayout()
        self.actual_kpi = self._create_kpi_card("当前已完成", "0 米")
        self.oee_kpi = self._create_kpi_card("实时OEE", "0.0 %")
        kpi_layout.addWidget(self.actual_kpi); kpi_layout.addWidget(self.oee_kpi)
        deviation_box = QGroupBox("计划-实际偏差分析")
        deviation_layout = QVBoxLayout(deviation_box)
        self.deviation_plot = pg.PlotWidget(); self.deviation_plot.setBackground(None)
        self.deviation_plot.showGrid(x=True, y=True, alpha=0.3)
        self.deviation_plot.getAxis('left').setTextPen('black'); self.deviation_plot.getAxis('bottom').setTextPen('black')
        self.deviation_plot.addLegend()
        self.plan_curve = self.deviation_plot.plot(pen='k', name='理论进度'); self.actual_curve = self.deviation_plot.plot(pen='c', name='实际进度')
        self.fill_item = pg.FillBetweenItem(self.actual_curve, self.plan_curve, brush=(100, 100, 255, 80)); self.deviation_plot.addItem(self.fill_item)
        deviation_layout.addWidget(self.deviation_plot)
        diagnosis_box = QGroupBox("智能调度建议")
        diagnosis_layout = QVBoxLayout(diagnosis_box)
        self.suggestion_label = QLabel("正在初始化分析..."); self.suggestion_label.setWordWrap(True)
        diagnosis_layout.addWidget(self.suggestion_label)
        layout.addLayout(kpi_layout); layout.addWidget(deviation_box); layout.addWidget(diagnosis_box)
        return panel

    def _create_kpi_card(self, title, value):
        card = QFrame(); card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("QFrame { background-color: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 5px; }")
        layout = QVBoxLayout(card); layout.setContentsMargins(20, 15, 20, 15)
        title_label = QLabel(title); title_label.setStyleSheet("color: #616161; font-size: 10pt;")
        value_label = QLabel(value); value_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: #212121;")
        layout.addWidget(title_label); layout.addWidget(value_label); card.value_label = value_label
        return card

    def update_ui(self, data):
        self.plan_kpi.value_label.setText(f"{int(data['total_plan']):,} 米")
        self.orders_kpi.value_label.setText(f"{data['pending_orders']} 个")
        self._update_gantt(data['schedule'])
        self.actual_kpi.value_label.setText(f"{int(data['actual_output']):,} 米")
        self.oee_kpi.value_label.setText(f"{data['oee']:.1f} %")
        self._update_deviation_chart(data.get('timestamp', 0), data['theoretical_output'], data['actual_output'])
        self._diagnose_schedule(data)
        
    def _update_gantt(self, schedule):
        self.gantt_plot.clear()
        lines = {'Line A': 0, 'Line B': 1}
        
        # --- 核心修正点：转换 Ticks 格式 ---
        # 格式应该是 [[(tick_value, tick_label), ...]]，所以我们需要交换 key 和 value
        ticks = [[(v, k) for k, v in lines.items()]]
        self.gantt_plot.getAxis('left').setTicks(ticks)
        
        self.gantt_plot.setYRange(-0.5, len(lines)-0.5, padding=0)
        self.gantt_plot.setXRange(0, 24, padding=0)
        self.gantt_plot.setTitle("甘特图预览")
        
        colors = [QColor(0, 200, 200, 150), QColor(200, 0, 200, 150)]
        for i, task in enumerate(schedule):
            y = lines.get(task['line'])
            if y is not None:
                bar = QGraphicsRectItem(task['start'], y - 0.4, task['end'] - task['start'], 0.8)
                bar.setBrush(QBrush(colors[i % len(colors)]))
                bar.setPen(pg.mkPen(None))
                bar.setToolTip(f"订单: {task['order']}")
                self.gantt_plot.addItem(bar)

    def _update_deviation_chart(self, timestamp, theoretical, actual):
        self.time_data.append(timestamp); self.theoretical_data.append(theoretical); self.actual_data.append(actual)
        if len(self.time_data) > 300:
            self.time_data.pop(0); self.theoretical_data.pop(0); self.actual_data.pop(0)
        self.plan_curve.setData(self.time_data, self.theoretical_data)
        self.actual_curve.setData(self.time_data, self.actual_data)
        self.fill_item.setBrush((255, 100, 100, 80) if actual < theoretical else (100, 255, 100, 80))

    def _diagnose_schedule(self, data):
        deviation = data['theoretical_output'] - data['actual_output']
        if deviation > 5000: suggestion = (f"<font color='#D32F2F'><b>严重落后...</b></font>")
        elif deviation > 1000: suggestion = (f"<font color='#F57C00'><b>进度落后...</b></font>")
        else: suggestion = "生产进度正常，在计划范围内。"
        self.suggestion_label.setText(suggestion)

    def closeEvent(self, event):
        self.simulator.stop(); super().closeEvent(event)