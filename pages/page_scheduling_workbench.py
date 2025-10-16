# pages/page_scheduling_workbench.py
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, 
                             QPushButton, QGroupBox, QListWidgetItem, QGraphicsRectItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import pyqtgraph as pg
import datetime # 确保导入 datetime

# 使用绝对路径导入
from widgets.order_card import OrderCard
from pages.widgets.scheduling_algorithm import HeuristicScheduler

class PageSchedulingWorkbench(QWidget):
    def __init__(self):
        super().__init__()
        
        self._load_mock_data()
        
        main_layout = QHBoxLayout(self); main_layout.setSpacing(15)
        
        left_panel = self._create_order_list_panel()
        right_panel = self._create_gantt_panel()
        
        main_layout.addWidget(left_panel, 1); main_layout.addWidget(right_panel, 3)

        self._refresh_order_list()

    def _create_order_list_panel(self):
        panel = QGroupBox("待排程订单 (按优先级排序)"); layout = QVBoxLayout(panel)
        self.order_list = QListWidget()
        run_scheduler_button = QPushButton("🚀 一键智能排程"); run_scheduler_button.setMinimumHeight(40)
        run_scheduler_button.clicked.connect(self._run_auto_scheduling)
        layout.addWidget(self.order_list); layout.addWidget(run_scheduler_button)
        return panel

    def _create_gantt_panel(self):
        panel = QGroupBox("生产线排程甘特图"); layout = QVBoxLayout(panel)
        self.gantt_plot = pg.PlotWidget(); self.gantt_plot.setBackground(None)
        self.gantt_plot.showGrid(x=True, y=True, alpha=0.3); self.gantt_plot.getAxis('left').setTextPen('black')
        self.gantt_plot.getAxis('bottom').setTextPen('black'); self.gantt_plot.setLabel('bottom', "时间 (小时)")
        
        self.resources = {'Line A (5mm)': 0, 'Line B (5mm/8mm)': 1, 'Line C (8mm)': 2}
        ticks = [[(v, k) for k, v in self.resources.items()]]
        self.gantt_plot.getAxis('left').setTicks(ticks); self.gantt_plot.setYRange(-0.5, len(self.resources)-0.5, padding=0)
        layout.addWidget(self.gantt_plot); return panel

    def _refresh_order_list(self):
        self.order_list.clear()
        pending_orders = [o for o in self.all_orders if o['status'] == 'ready']
        pending_orders.sort(key=lambda o: o.get('priority', 0), reverse=True)
        for order in pending_orders:
            card = OrderCard(order); item = QListWidgetItem()
            item.setSizeHint(card.sizeHint()); self.order_list.addItem(item)
            self.order_list.setItemWidget(item, card)

    def _run_auto_scheduling(self):
        pending_orders = [o for o in self.all_orders if o['status'] == 'ready']
        if not pending_orders: return
        resources_info = {
            'Line A (5mm)': {'specs': ['5mm']}, 'Line B (5mm/8mm)': {'specs': ['5mm', '8mm']}, 'Line C (8mm)': {'specs': ['8mm']}
        }
        scheduler = HeuristicScheduler(pending_orders, resources_info); schedule_result = scheduler.run()
        self._draw_schedule(schedule_result)
        for order in pending_orders: order['status'] = 'scheduled'
        self._refresh_order_list()

    def _draw_schedule(self, schedule):
        self.gantt_plot.clear()
        colors = [QColor(0, 200, 200, 150), QColor(200, 0, 200, 150), QColor(200, 200, 0, 150)]
        for i, (line_name, tasks) in enumerate(schedule.items()):
            y = self.resources[line_name]
            for task in tasks:
                bar = QGraphicsRectItem(task['start'], y - 0.4, task['end'] - task['start'], 0.8)
                bar.setBrush(QBrush(colors[i % len(colors)])); bar.setPen(pg.mkPen(None))
                bar.setToolTip(f"订单: {task['order']['id']}\n产品: {task['order']['product']}")
                self.gantt_plot.addItem(bar)
                text = pg.TextItem(task['order']['id'], anchor=(0, 0.5)); text.setPos(task['start'] + 0.1, y)
                self.gantt_plot.addItem(text)

    # --- 核心修正点：补全所有模拟数据的字段 ---
    def _load_mock_data(self):
        today = datetime.date.today()
        self.all_orders = [
            {"id": "ORD-001", "product": "5mm 微喷带", "quantity": 5000, "due_date": today + datetime.timedelta(days=8), "customer_level": "A", "status": "ready", "priority": 95},
            {"id": "ORD-002", "product": "8mm 微喷带", "quantity": 8000, "due_date": today + datetime.timedelta(days=10), "customer_level": "B", "status": "ready", "priority": 38},
            {"id": "ORD-003", "product": "5mm 微喷带", "quantity": 12000, "due_date": today + datetime.timedelta(days=12), "customer_level": "C", "status": "scheduled", "priority": 20},
            {"id": "ORD-004", "product": "8mm 微喷带", "quantity": 3000, "due_date": today + datetime.timedelta(days=5), "customer_level": "A", "status": "ready", "priority": 80},
            {"id": "ORD-005", "product": "5mm 微喷带", "quantity": 7000, "due_date": today + datetime.timedelta(days=7), "customer_level": "B", "status": "ready", "priority": 65},
        ]