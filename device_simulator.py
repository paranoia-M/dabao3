# device_simulator.py
import time
import random
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime, timedelta

class SchedulingSimulatorThread(QThread):
    """模拟排程与调度系统的后台数据流"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True
        
        # 模拟计划数据
        self.total_plan_output = 50000
        self.pending_orders = 5
        self.schedule = [
            {'line': 'Line A', 'order': 'WO-001', 'start': 0, 'end': 8},
            {'line': 'Line B', 'order': 'WO-002', 'start': 2, 'end': 10},
            {'line': 'Line A', 'order': 'WO-003', 'start': 9, 'end': 15},
            {'line': 'Line B', 'order': 'WO-004', 'start': 11, 'end': 20},
        ]
        
        # 模拟执行数据
        self.start_time = time.time()
        self.current_output = 0
        self.oee = 85.0
        self.devices_status = { '挤出机 A': 'running', '挤出机 B': 'running', '牵引机 A': 'running' }

    def run(self):
        while self.is_running:
            elapsed_seconds = time.time() - self.start_time
            
            # 理论应完成产量 (假设8小时完成总计划)
            theoretical_output = min(self.total_plan_output, (self.total_plan_output / (8 * 3600)) * elapsed_seconds)
            
            # 模拟实际产量 (随机波动，可能落后或超前)
            if self.current_output < self.total_plan_output:
                self.current_output += random.uniform(1.5, 2.5) * 5 # 增加波动性
            
            # 模拟OEE波动
            self.oee += random.uniform(-0.5, 0.5); self.oee = max(60, min(95, self.oee))

            data_packet = {
                'total_plan': self.total_plan_output,
                'pending_orders': self.pending_orders,
                'schedule': self.schedule,
                'theoretical_output': theoretical_output,
                'actual_output': self.current_output,
                'oee': self.oee,
                'devices_status': self.devices_status,
                'timestamp': elapsed_seconds
            }
            self.data_updated.emit(data_packet)
            
            time.sleep(1) # 每秒更新

    def stop(self):
        self.is_running = False; self.quit(); self.wait()