# pages/page_orders.py
import random
from functools import partial # 导入partial
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton, QLineEdit, QComboBox, QMenu, QMessageBox,
                             QProgressBar, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from .widgets.order_dialog import OrderDialog

class PageOrders(QWidget):
    def __init__(self):
        super().__init__()
        
        self.orders_data = self._create_mock_data()
        self.current_filter_text = ""
        self.current_filter_status = "所有状态"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        controls_layout = self._create_controls_layout()
        main_layout.addLayout(controls_layout)

        self.table = QTableWidget()
        # --- 1. 增加列数 ---
        self.table.setColumnCount(7) 
        # --- 2. 增加“操作”列标题 ---
        self.table.setHorizontalHeaderLabels(["工单ID", "产品名称", "计划数量", "完成进度", "状态", "创建日期", "操作"])
        
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # --- 3. 设置最后一列的宽度模式 ---
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # 操作列自适应内容宽度
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        # --- 4. 增加双击事件 ---
        self.table.cellDoubleClicked.connect(self._handle_double_click)

        main_layout.addWidget(self.table)
        
        self._populate_table()

    # _create_controls_layout 方法保持不变
    def _create_controls_layout(self):
        layout = QHBoxLayout()
        add_button = QPushButton("＋ 新建工单")
        add_button.clicked.connect(self._show_add_dialog)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("按工单ID或产品名称搜索...")
        self.search_input.textChanged.connect(self._filter_table)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["所有状态", "待处理", "生产中", "已完成", "已取消"])
        self.status_filter.currentIndexChanged.connect(self._filter_table)
        layout.addWidget(add_button)
        layout.addStretch()
        layout.addWidget(QLabel("筛选:"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.status_filter)
        return layout

    def _populate_table(self):
        self.table.setRowCount(0)
        filtered_data = self._get_filtered_data()

        for row, order in enumerate(filtered_data):
            self.table.insertRow(row)
            
            # ... (前5列的逻辑保持不变)
            status_colors = {"待处理": QColor("#FFC107"), "生产中": QColor("#00BCD4"), "已完成": QColor("#4CAF50"), "已取消": QColor("#F44336")}
            self.table.setItem(row, 0, QTableWidgetItem(order["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(order["product"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"{order['quantity_plan']} 米"))
            progress = QProgressBar(); progress.setRange(0, 100); percentage = (order["quantity_done"] / order["quantity_plan"]) * 100; progress.setValue(int(percentage)); progress.setFormat(f"{order['quantity_done']} / {order['quantity_plan']}"); progress.setAlignment(Qt.AlignCenter); self.table.setCellWidget(row, 3, progress)
            status_item = QTableWidgetItem(order["status"]); status_item.setBackground(status_colors.get(order["status"], QColor("white"))); self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, QTableWidgetItem(order["date"]))
            
            # --- 5. 创建并添加操作按钮 ---
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            view_button = QPushButton("查看")
            edit_button = QPushButton("编辑")
            delete_button = QPushButton("删除")
            
            # 使用 functools.partial 将当前行的 order_id 传递给槽函数
            view_button.clicked.connect(partial(self._view_order, order["id"]))
            edit_button.clicked.connect(partial(self._edit_order, order["id"]))
            delete_button.clicked.connect(partial(self._delete_order, order["id"]))
            
            actions_layout.addWidget(view_button)
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            
            self.table.setCellWidget(row, 6, actions_widget)

    # _get_filtered_data, _filter_table, _show_add_dialog 保持不变
    def _get_filtered_data(self):
        data = self.orders_data
        if self.current_filter_status != "所有状态": data = [o for o in data if o["status"] == self.current_filter_status]
        if self.current_filter_text: text = self.current_filter_text.lower(); data = [o for o in data if text in o["id"].lower() or text in o["product"].lower()]
        return data
    def _filter_table(self):
        self.current_filter_text = self.search_input.text(); self.current_filter_status = self.status_filter.currentText(); self._populate_table()
    def _show_add_dialog(self):
        dialog = OrderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data(); new_data["quantity_done"] = 0; new_data["date"] = "2023-10-28"; self.orders_data.append(new_data); self._populate_table()

    # _show_context_menu 保持不变 (作为辅助功能)
    def _show_context_menu(self, pos):
        selected_items = self.table.selectedItems();
        if not selected_items: return
        selected_row = self.table.row(selected_items[0]); order_id = self.table.item(selected_row, 0).text()
        menu = QMenu(); edit_action = menu.addAction("编辑"); delete_action = menu.addAction("删除"); menu.addSeparator(); status_menu = menu.addMenu("更改状态"); start_action = status_menu.addAction("开始生产"); complete_action = status_menu.addAction("标记为完成"); cancel_action = status_menu.addAction("取消工单")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action: self._edit_order(order_id)
        elif action == delete_action: self._delete_order(order_id)
        elif action == start_action: self._change_order_status(order_id, "生产中")
        elif action == complete_action: self._change_order_status(order_id, "已完成")
        elif action == cancel_action: self._change_order_status(order_id, "已取消")
        
    # --- 6. 新增“查看”和“双击”的槽函数 ---
    def _view_order(self, order_id):
        """查看指定ID的工单详情"""
        order_to_view = next((o for o in self.orders_data if o["id"] == order_id), None)
        if not order_to_view: return
        
        dialog = OrderDialog(self, order_data=order_to_view, view_only=True)
        dialog.exec_()

    def _handle_double_click(self, row, column):
        """处理双击事件，默认为查看详情"""
        order_id = self.table.item(row, 0).text()
        self._view_order(order_id)

    # _edit_order, _delete_order, _change_order_status, _create_mock_data 保持不变
    def _edit_order(self, order_id):
        order_to_edit = next((o for o in self.orders_data if o["id"] == order_id), None)
        if not order_to_edit: return
        dialog = OrderDialog(self, order_data=order_to_edit)
        if dialog.exec_() == QDialog.Accepted: updated_data = dialog.get_data(); order_to_edit.update(updated_data); self._populate_table()
    def _delete_order(self, order_id):
        reply = QMessageBox.question(self, "确认删除", f"您确定要删除工单 {order_id} 吗？\n此操作不可撤销。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: self.orders_data = [o for o in self.orders_data if o["id"] != order_id]; self._populate_table()
    def _change_order_status(self, order_id, new_status):
        order_to_change = next((o for o in self.orders_data if o["id"] == order_id), None)
        if not order_to_change: return
        if new_status == "已完成": order_to_change["quantity_done"] = order_to_change["quantity_plan"]
        order_to_change["status"] = new_status; self._populate_table()
    def _create_mock_data(self):
        return [{"id": "WO-20231027-001", "product": "5mm 滴灌管 (黑色)", "quantity_plan": 5000, "quantity_done": 5000, "status": "已完成", "date": "2023-10-27"}, {"id": "WO-20231027-002", "product": "8mm 滴灌管 (蓝色)", "quantity_plan": 8000, "quantity_done": 3200, "status": "生产中", "date": "2023-10-27"}, {"id": "WO-20231028-001", "product": "5mm 滴灌管 (黑色)", "quantity_plan": 12000, "quantity_done": 0, "status": "待处理", "date": "2023-10-28"}, {"id": "WO-20231026-003", "product": "压力补偿滴头", "quantity_plan": 25000, "quantity_done": 0, "status": "已取消", "date": "2023-10-26"}, {"id": "WO-20231028-002", "product": "12mm PE管", "quantity_plan": 7500, "quantity_done": 1500, "status": "生产中", "date": "2023-10-28"}]