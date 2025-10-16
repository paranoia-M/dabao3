# pages/page_mes_cockpit.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QPushButton, QProgressBar, QMessageBox, QInputDialog, 
                             QListWidget, QListWidgetItem, QGroupBox, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import Qt, QTimer, QTime, QThread
from PyQt5.QtGui import QColor, QBrush
import time, random, os
from playsound import playsound

from device_simulator import SchedulingSimulatorThread
# --- 核心修正点 3: 确保导入的类名与 mes_widgets.py 中定义的 PacingGauge 一致 ---
from .widgets.mes_widgets import PacingGauge 

# LineMonitor 类现在依赖 OEEGauge，但我们把它放在主类内部
class LineMonitor(QFrame):
    """单条生产线的监控面板"""
    def __init__(self, line_name, parent_page):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.line_name = line_name
        self.parent_page = parent_page
        
        layout = QHBoxLayout(self)
        self.andon_light = QLabel(); self.andon_light.setFixedSize(40, 40)
        wo_layout = QVBoxLayout()
        self.wo_id_label = QLabel("<b>工单:</b> N/A")
        self.progress_bar = QProgressBar()
        wo_layout.addWidget(self.wo_id_label); wo_layout.addWidget(self.progress_bar)
        
        # --- 核心修正点 4: 此处也应该使用 PacingGauge ---
        self.oee_gauge = PacingGauge() # 使用 PacingGauge, 而不是 OEEGauge
        
        self.eta_label = QLabel("ETA: --:--:--")
        self.call_button = QPushButton("呼叫"); self.call_button.clicked.connect(self.handle_call)
        
        layout.addWidget(self.andon_light); layout.addLayout(wo_layout, 2)
        layout.addWidget(self.oee_gauge, 1); layout.addWidget(self.eta_label, 1)
        layout.addWidget(self.call_button, 1)
        
    def update_data(self, line_data):
        status = line_data['status']
        colors = {'running': 'green', 'idle': 'orange', 'fault': 'red', 'call': 'yellow'}
        self.andon_light.setStyleSheet(f"background-color: {colors.get(status, 'gray')}; border-radius: 20px;")
        self.wo_id_label.setText(f"<b>工单:</b> {line_data['wo_id']}")
        self.progress_bar.setValue(int(line_data['progress']))
        self.oee_gauge.set_value(line_data['cycle_time']) # 传递 cycle_time
        
        if line_data['eta']: self.eta_label.setText(f"ETA: {line_data['eta'].toString('HH:mm:ss')}")
        else: self.eta_label.setText("ETA: --:--:--")
            
    def handle_call(self):
        reasons = ["缺料", "质量异常", "设备小故障", "需要技术支持"]
        reason, ok = QInputDialog.getItem(self, "呼叫", "请选择呼叫原因:", reasons, 0, False)
        if ok and reason:
            self.parent_page.log_event(f"[{QTime.currentTime().toString('HH:mm:ss')}] {self.line_name} 呼叫: {reason}")
            self.update_data({'status': 'call', 'wo_id': self.wo_id_label.text().split(':')[-1].strip(), 
                              'progress': self.progress_bar.value(), 'cycle_time': self.oee_gauge.takt_time, 'eta': None})


class PageMesCockpit(QWidget):
    def __init__(self):
        super().__init__()
        self.last_unit_times = {"Line A": 0, "Line B": 0}

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(20, 20, 20, 20)
        self.lines = {"Line A": LineMonitor("Line A", self), "Line B": LineMonitor("Line B", self)}
        for line_monitor in self.lines.values(): main_layout.addWidget(line_monitor)
        
        log_box = QGroupBox("事件日志"); log_layout = QVBoxLayout(log_box)
        self.log_list = QListWidget(); log_layout.addWidget(self.log_list); main_layout.addWidget(log_box)
        
        self.simulator = SchedulingSimulatorThread(self); self.simulator.data_updated.connect(self.update_ui); self.simulator.start()

    def update_ui(self, data):
        current_time = time.time()
        # Line A logic
        if self.last_unit_times["Line A"] == 0: self.last_unit_times["Line A"] = current_time
        cycle_time_a = self.lines["Line A"].oee_gauge.takt_time # default
        if random.random() < 0.2: cycle_time_a = current_time - self.last_unit_times["Line A"]; self.last_unit_times["Line A"] = current_time
        self.lines["Line A"].update_data({
            'status': 'running' if data['oee'] > 80 else 'idle', 'wo_id': data['schedule'][0]['order'],
            'progress': (data['actual_output'] / 25000) * 100 if data['actual_output'] < 25000 else 100,
            'cycle_time': cycle_time_a, 'eta': QTime.currentTime().addSecs(random.randint(3600, 7200))
        })
        
        # Line B logic
        if self.last_unit_times["Line B"] == 0: self.last_unit_times["Line B"] = current_time
        is_b_fault = random.random() < 0.1 or (hasattr(self, 'b_is_fault') and self.b_is_fault); self.b_is_fault = is_b_fault
        cycle_time_b = self.lines["Line B"].oee_gauge.takt_time * 1.5 # Slower
        if not is_b_fault and random.random() < 0.1: cycle_time_b = current_time - self.last_unit_times["Line B"]; self.last_unit_times["Line B"] = current_time
        self.lines["Line B"].update_data({
            'status': 'fault' if is_b_fault else 'idle', 'wo_id': data['schedule'][1]['order'],
            'progress': 30, 'cycle_time': cycle_time_b, 'eta': None
        })
        
        if is_b_fault and (self.log_list.count() == 0 or "故障" not in self.log_list.item(0).text()):
            self.log_event(f"[{QTime.currentTime().toString('HH:mm:ss')}] 严重: Line B 发生未知故障！", 'red')
            QThread.create(self.play_alarm).start()
            
    def log_event(self, message, color_name=None):
        item = QListWidgetItem(message); 
        if color_name: item.setForeground(QColor(color_name))
        self.log_list.insertItem(0, item)
        if self.log_list.count() > 100: self.log_list.takeItem(100)

    def play_alarm(self):
        alarm_file = os.path.join("assets", "alarm.wav")
        try:
            if os.path.exists(alarm_file): playsound(alarm_file)
        except Exception as e: print(f"无法播放声音: {e}")
            
    def closeEvent(self, event):
        self.simulator.stop(); super().closeEvent(event)