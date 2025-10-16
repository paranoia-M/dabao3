# pages/page_schedule.py
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, 
                             QPushButton, QFrame, QListWidgetItem)
from PyQt5.QtCore import Qt

from .widgets.gantt_chart import ScheduleGanttView, TaskBlockItem

class PageSchedule(QWidget):
    def __init__(self):
        super().__init__()
        
        self.production_lines = ["滴灌管生产线 A", "滴灌管生产线 B", "PE管生产线", "滴头生产线"]
        self.unscheduled_orders, self.scheduled_orders = self._create_mock_data()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)
        
        self.gantt_view = ScheduleGanttView(self.production_lines)
        main_layout.addWidget(self.gantt_view, 1)
        
        # --- 1. 将所有信号连接都集中在这里 ---
        self.gantt_view.task_dropped.connect(self.handle_task_scheduled)
        self.gantt_view.task_rescheduled.connect(self.handle_task_rescheduled)
        
        self._populate_unscheduled_list()
        self._populate_gantt_chart()

    def _create_left_panel(self):
        panel = QFrame(); panel.setFixedWidth(250); panel.setStyleSheet("background-color: #263238; border-right: 1px solid #455A64;")
        layout = QVBoxLayout(panel); layout.setContentsMargins(10, 10, 10, 10)
        title = QLabel("未排程工单"); title.setStyleSheet("font-size: 14pt; color: white; padding-bottom: 10px;"); layout.addWidget(title)
        self.unscheduled_list = QListWidget(); self.unscheduled_list.setDragEnabled(True); layout.addWidget(self.unscheduled_list)
        zoom_label = QLabel("时间轴缩放"); zoom_label.setStyleSheet("color: white; padding-top: 10px;"); layout.addWidget(zoom_label)
        zoom_buttons_layout = QHBoxLayout(); zoom_24h = QPushButton("24小时"); zoom_7d = QPushButton("7天")
        zoom_24h.clicked.connect(lambda: self._update_gantt_zoom(24)); zoom_7d.clicked.connect(lambda: self._update_gantt_zoom(24 * 7))
        zoom_buttons_layout.addWidget(zoom_24h); zoom_buttons_layout.addWidget(zoom_7d); layout.addLayout(zoom_buttons_layout)
        return panel

    def _populate_unscheduled_list(self):
        self.unscheduled_list.clear()
        for order in self.unscheduled_orders:
            item = QListWidgetItem(f"{order['id']}\n{order['product']} ({order['duration_hours']}h)"); item.setData(Qt.UserRole, order['id']); self.unscheduled_list.addItem(item)
            
    def _populate_gantt_chart(self):
        for order in self.scheduled_orders:
            # --- 2. 这里不再需要连接信号了 ---
            self.gantt_view.add_task(order, order['line'], order['start_hour'], order['duration_hours'])

    def handle_task_scheduled(self, order_id, line_index, start_hour):
        order_to_schedule = next((o for o in self.unscheduled_orders if o['id'] == order_id), None)
        if not order_to_schedule: return
        
        order_to_schedule['line'] = line_index
        order_to_schedule['start_hour'] = start_hour
        
        new_task_item = self.gantt_view.add_task(order_to_schedule, line_index, start_hour, order_to_schedule['duration_hours'])

        scene = self.gantt_view.scene
        all_other_tasks = [item for item in scene.items() if isinstance(item, TaskBlockItem) and item is not new_task_item]
        
        has_conflict = False
        for task in all_other_tasks:
            if new_task_item.collidesWithItem(task): has_conflict = True; break

        if has_conflict:
            print(f"冲突！无法排程工单 {order_id}。"); scene.removeItem(new_task_item)
        else:
            print(f"成功！工单 {order_id} 已排程。"); self.unscheduled_orders.remove(order_to_schedule); self.scheduled_orders.append(order_to_schedule); self._populate_unscheduled_list()
            
    def handle_task_rescheduled(self, order_id, new_line, new_hour):
        order_to_update = next((o for o in self.scheduled_orders if o['id'] == order_id), None)
        if order_to_update:
            order_to_update['line'] = new_line
            order_to_update['start_hour'] = new_hour
            print("数据模型已更新。")

    def _update_gantt_zoom(self, total_hours):
        self.gantt_view.set_total_hours(total_hours)
        self._populate_gantt_chart()
        
    def _create_mock_data(self):
        unscheduled = [{"id": "WO-20231028-001", "product": "5mm 滴灌管", "duration_hours": 8}, {"id": "WO-20231028-002", "product": "12mm PE管", "duration_hours": 5}]
        scheduled = [{"id": "WO-20231027-001", "product": "5mm 滴灌管", "duration_hours": 6, "line": 0, "start_hour": 1}, {"id": "WO-20231027-002", "product": "8mm 滴灌管", "duration_hours": 4, "line": 1, "start_hour": 3}, {"id": "WO-20231026-003", "product": "压力补偿滴头", "duration_hours": 7, "line": 3, "start_hour": 8}]
        return unscheduled, scheduled