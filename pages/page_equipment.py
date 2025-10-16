# pages/page_equipment.py
from collections import deque
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QListWidget, QListWidgetItem, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pyqtgraph as pg

# 导入我们的数据模拟器线程
from device_simulator import DeviceSimulatorThread

class StatusPanel(QFrame):
    """显示设备状态的面板"""
    def __init__(self, title):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14pt; color: white;")
        self.value_label = QLabel("N/A")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: white;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.set_status('normal')

    def set_value(self, text):
        self.value_label.setText(text)
        
    def set_status(self, status):
        colors = {'normal': '#388E3C', 'warning': '#FBC02D', 'fault': '#D32F2F'}
        self.setStyleSheet(f"background-color: {colors.get(status, 'gray')}; border-radius: 8px;")

class PageEquipment(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- 数据存储 ---
        self.max_data_points = 60
        self.temp_data = deque(maxlen=self.max_data_points)
        self.pressure_data = deque(maxlen=self.max_data_points)
        self.speed_data = deque(maxlen=self.max_data_points)
        self.time_labels = deque(maxlen=self.max_data_points)
        self.last_status = 'normal'
        
        # --- UI 布局 ---
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)
        
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        
        charts_widget = self._create_charts_widget()
        status_widget = self._create_status_widget()
        
        top_layout.addWidget(charts_widget, 3)
        top_layout.addWidget(status_widget, 1)
        
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_title = QLabel("报警日志")
        bottom_title.setStyleSheet("font-size: 14pt; color: white;")
        self.alarm_log_list = QListWidget()
        bottom_layout.addWidget(bottom_title)
        bottom_layout.addWidget(self.alarm_log_list)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        
        main_layout.addWidget(splitter)
        
        # --- 启动后台数据线程 ---
        self.simulator_thread = DeviceSimulatorThread(self)
        self.simulator_thread.data_updated.connect(self.update_dashboard)
        self.simulator_thread.start()

    def _create_charts_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # --- 1. 修改：创建图表控件和曲线对象 ---
        # 我们需要分别存储 PlotWidget (用于布局) 和 PlotDataItem (用于更新数据)
        temp_plot_widget, self.temp_curve = self._create_plot("实时温度 (°C)", (80, 100), '#FFB300')
        pressure_plot_widget, self.pressure_curve = self._create_plot("实时压力 (MPa)", (1, 4), '#03A9F4')
        speed_plot_widget, self.speed_curve = self._create_plot("生产速度 (m/min)", (0, 70), '#8BC34A')
        
        # --- 2. 修改：将 PlotWidget 添加到布局中 ---
        layout.addWidget(temp_plot_widget)
        layout.addWidget(pressure_plot_widget)
        layout.addWidget(speed_plot_widget)
        
        return widget
        
    def _create_plot(self, title, range_y, color):
        """此方法现在返回一个元组: (PlotWidget, PlotDataItem)"""
        plot_widget = pg.PlotWidget() # 这是QWidget
        plot_widget.setBackground('#263238')
        plot_widget.setTitle(title, color="#B0BEC5", size="12pt")
        plot_widget.setYRange(*range_y)
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        pen = pg.mkPen(color=color, width=2)
        curve = plot_widget.plot(pen=pen) # 这是PlotDataItem
        
        # --- 3. 修改：返回控件和曲线的元组 ---
        return (plot_widget, curve)

    def _create_status_widget(self):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setSpacing(15)
        self.main_status_panel = StatusPanel("设备总状态")
        self.temp_value_label = QLabel("温度: N/A"); self.pressure_value_label = QLabel("压力: N/A"); self.speed_value_label = QLabel("速度: N/A")
        layout.addWidget(self.main_status_panel); layout.addWidget(self.temp_value_label); layout.addWidget(self.pressure_value_label); layout.addWidget(self.speed_value_label); layout.addStretch()
        return widget

    def update_dashboard(self, data):
        self.temp_data.append(data['temperature']); self.pressure_data.append(data['pressure']); self.speed_data.append(data['speed']); self.time_labels.append(data['timestamp'])
        
        # --- 4. 修改：使用正确的曲线对象来更新数据 ---
        self.temp_curve.setData(list(self.temp_data))
        self.pressure_curve.setData(list(self.pressure_data))
        self.speed_curve.setData(list(self.speed_data))

        self.temp_value_label.setText(f"温度: {data['temperature']:.1f} °C"); self.pressure_value_label.setText(f"压力: {data['pressure']:.2f} MPa"); self.speed_value_label.setText(f"速度: {data['speed']:.1f} m/min")

        status, message = self._evaluate_status(data)
        
        self.main_status_panel.set_value(message); self.main_status_panel.set_status(status)

        if status != 'normal' and status != self.last_status:
            log_item = QListWidgetItem(f"[{data['timestamp']}] {message}")
            if status == 'warning': log_item.setForeground(QColor('#FBC02D'))
            elif status == 'fault': log_item.setForeground(QColor('#D32F2F'))
            self.alarm_log_list.insertItem(0, log_item)
            if self.alarm_log_list.count() > 100: self.alarm_log_list.takeItem(100)
                
        self.last_status = status

    def _evaluate_status(self, data):
        temp = data['temperature']; pressure = data['pressure']; speed = data['speed']
        if pressure > 2.5 and speed > 10: return 'fault', "压力过载！"
        if speed < 1 and pressure > 0.5: return 'fault', "堵料故障！"
        if temp > 98: return 'fault', "温度严重超标！"
        if temp > 95: return 'warning', "温度偏高"
        if pressure > 2.2: return 'warning', "压力偏高"
        if speed < 40 and speed > 1: return 'warning', "速度过慢"
        return 'normal', "运行正常"

    def closeEvent(self, event):
        print("关闭设备监控页面，正在停止模拟器线程...")
        self.simulator_thread.stop()
        super().closeEvent(event)