# pages/page_order_pool.py
import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QPushButton, QGroupBox, QVBoxLayout, QDialog,
                             QMessageBox, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from widgets.order_card import OrderCard
from widgets.order_dialog import OrderDialog

class PageOrderPool(QWidget):
    def __init__(self):
        super().__init__()
        self.orders = self._create_mock_data()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        controls = QHBoxLayout()
        controls.addWidget(QLabel("<h2>安全订单需求管理</h2>")); controls.addStretch()
        add_button = QPushButton("＋ 新增订单"); add_button.clicked.connect(self._add_order)
        controls.addWidget(add_button)
        main_layout.addLayout(controls)

        kanban_layout = QHBoxLayout()
        self.lanes = {
            "new": self._create_lane("新订单"),
            "approved": self._create_lane("已审核"),
            "ready": self._create_lane("待排程")
        }
        for name, lane_box in self.lanes.items(): 
            kanban_layout.addWidget(lane_box)
            lane_box.findChild(QListWidget).setObjectName(name)
        main_layout.addLayout(kanban_layout)

        self._refresh_kanban()

    def _create_lane(self, title):
        box = QGroupBox(title); layout = QVBoxLayout(box)
        list_widget = QListWidget()
        list_widget.setDragDropMode(QListWidget.DragDrop)
        list_widget.setDefaultDropAction(Qt.MoveAction)
        list_widget.setSpacing(10)
        list_widget.setStyleSheet("QListWidget::item:selected { border: 2px solid #0288D1; }")
        list_widget.model().rowsMoved.connect(self._on_item_moved)
        layout.addWidget(list_widget); return box

    def _refresh_kanban(self):
        for lane_box in self.lanes.values():
            lane_box.findChild(QListWidget).clear()
        
        for order in self.orders:
            card = OrderCard(order)
            # --- 核心交互 1: 连接卡片的右键菜单信号 ---
            card.request_context_menu.connect(self._show_context_menu)
            
            item = QListWidgetItem(); item.setSizeHint(card.sizeHint()); item.setData(Qt.UserRole, order['id'])
            lane_box = self.lanes.get(order['status'])
            if lane_box:
                list_widget = lane_box.findChild(QListWidget)
                list_widget.addItem(item); list_widget.setItemWidget(item, card)

    def _on_item_moved(self, parent, start, end, dest, row):
        target_list_widget = self.sender().parent();
        if not target_list_widget: return
        item = target_list_widget.item(row);
        if not item: return
        order_id = item.data(Qt.UserRole); order = next((o for o in self.orders if o['id'] == order_id), None)
        if order:
            new_status = target_list_widget.objectName()
            if order['status'] != new_status: order['status'] = new_status

    def _show_context_menu(self, order_id, event):
        """核心交互 2: 创建并显示动态的右键菜单"""
        order = next((o for o in self.orders if o['id'] == order_id), None)
        if not order: return

        menu = QMenu(self)
        
        # --- 根据状态动态生成菜单项 ---
        if order['status'] == 'new':
            approve_action = menu.addAction("✔️ 审核通过")
            approve_action.triggered.connect(lambda: self._change_order_status(order_id, 'approved'))
        elif order['status'] == 'approved':
            ready_action = menu.addAction("📦 标记为已备料")
            revert_action = menu.addAction("⏪ 撤销审核")
            ready_action.triggered.connect(lambda: self._change_order_status(order_id, 'ready'))
            revert_action.triggered.connect(lambda: self._change_order_status(order_id, 'new'))
        elif order['status'] == 'ready':
            unready_action = menu.addAction("⏪ 撤销备料")
            unready_action.triggered.connect(lambda: self._change_order_status(order_id, 'approved'))

        menu.addSeparator()
        edit_action = menu.addAction("✏️ 编辑订单"); edit_action.triggered.connect(lambda: self._edit_order(order_id))
        delete_action = menu.addAction("❌ 删除订单"); delete_action.triggered.connect(lambda: self._delete_order(order_id))

        # 在鼠标点击的位置显示菜单
        menu.exec_(event.globalPos())

    def _change_order_status(self, order_id, new_status):
        """核心交互 3: 处理状态流转"""
        order = next((o for o in self.orders if o['id'] == order_id), None)
        if order:
            order['status'] = new_status
            self._refresh_kanban() # 重新渲染整个看板以移动卡片

    def _add_order(self):
        dialog = OrderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data.get('id'): data['id'] = f"ORD-{len(self.orders) + 5:03d}"
            data['status'] = 'new'; data['priority'] = self._calculate_priority_score(data)
            self.orders.append(data); self._refresh_kanban()
            
    def _edit_order(self, order_id):
        order = next((o for o in self.orders if o['id'] == order_id), None)
        if not order: return
        
        dialog = OrderDialog(self, order_data=order)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            order.update(updated_data)
            # 重新计算优先级并刷新
            order['priority'] = self._calculate_priority_score(order)
            self._refresh_kanban()

    def _delete_order(self, order_id):
        reply = QMessageBox.question(self, "确认删除", f"您确定要删除订单 {order_id} 吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.orders = [o for o in self.orders if o['id'] != order_id]
            self._refresh_kanban()

    def _calculate_priority_score(self, order_data):
        score = 0; days_left = (order_data['due_date'] - datetime.date.today()).days
        if days_left < 0: days_left = 0
        score += max(0, 50 - days_left * 5)
        level_score = {'A': 40, 'B': 20, 'C': 5}
        score += level_score.get(order_data['customer_level'], 0)
        score += order_data['quantity'] / 1000.0
        return int(min(100, score))

    def _create_mock_data(self):
        today = datetime.date.today()
        data = [
            {"id": "ORD-001", "product": "5mm 微喷带 (高压型)", "quantity": 5000, "due_date": today + datetime.timedelta(days=2), "customer_level": "A", "status": "new"},
            {"id": "ORD-002", "product": "8mm 微喷带 (标准型)", "quantity": 8000, "due_date": today + datetime.timedelta(days=10), "customer_level": "B", "status": "new"},
            {"id": "ORD-003", "product": "5mm 微喷带 (薄壁型)", "quantity": 12000, "due_date": today + datetime.timedelta(days=5), "customer_level": "C", "status": "approved"},
            {"id": "ORD-004", "product": "8mm 微喷带 (标准型)", "quantity": 20000, "due_date": today + datetime.timedelta(days=15), "customer_level": "B", "status": "ready"},
        ]
        for order in data: order['priority'] = self._calculate_priority_score(order)
        return data