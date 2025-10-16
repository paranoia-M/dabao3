# pages/page_materials.py
from functools import partial
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton, QLineEdit, QComboBox, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from .widgets.material_dialog import MaterialDialog
from .widgets.stock_operation_dialog import StockOperationDialog

class PageMaterials(QWidget):
    def __init__(self):
        super().__init__()
        
        self.materials_data = self._create_mock_data()
        self.current_filter_text = ""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        controls_layout = self._create_controls_layout()
        main_layout.addLayout(controls_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["物料编码", "物料名称", "类别", "当前库存", "安全库存", "单位", "操作"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        main_layout.addWidget(self.table)
        self._populate_table()

    def _create_controls_layout(self):
        layout = QHBoxLayout()
        add_button = QPushButton("＋ 添加物料")
        add_button.clicked.connect(self._show_add_dialog)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("按编码或名称搜索...")
        self.search_input.textChanged.connect(self._filter_table)
        
        layout.addWidget(add_button)
        layout.addStretch()
        layout.addWidget(QLabel("搜索:"))
        layout.addWidget(self.search_input)
        return layout

    def _populate_table(self):
        self.table.setRowCount(0)
        filtered_data = self._get_filtered_data()

        for row, material in enumerate(filtered_data):
            self.table.insertRow(row)
            
            # --- 特色逻辑 1: 安全库存预警 ---
            is_low_stock = material['current_stock'] < material['safety_stock']
            low_stock_color = QColor(255, 204, 203) # 淡红色
            
            self.table.setItem(row, 0, QTableWidgetItem(material["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(material["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(material["category"]))
            
            stock_item = QTableWidgetItem(str(material["current_stock"]))
            if is_low_stock:
                stock_item.setBackground(low_stock_color)
            self.table.setItem(row, 3, stock_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(str(material["safety_stock"])))
            self.table.setItem(row, 5, QTableWidgetItem(material["unit"]))
            
            self._create_action_buttons(row, material)

    def _create_action_buttons(self, row, material):
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)

        stock_in_button = QPushButton("入库")
        stock_out_button = QPushButton("出库")
        edit_button = QPushButton("编辑")
        delete_button = QPushButton("删除")
        
        material_id = material["id"]
        stock_in_button.clicked.connect(partial(self._show_stock_operation_dialog, material_id, 'in'))
        stock_out_button.clicked.connect(partial(self._show_stock_operation_dialog, material_id, 'out'))
        edit_button.clicked.connect(partial(self._show_edit_dialog, material_id))
        delete_button.clicked.connect(partial(self._delete_material, material_id))

        actions_layout.addWidget(stock_in_button)
        actions_layout.addWidget(stock_out_button)
        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        
        self.table.setCellWidget(row, 6, actions_widget)

    def _get_filtered_data(self):
        if not self.current_filter_text:
            return self.materials_data
        text = self.current_filter_text.lower()
        return [m for m in self.materials_data if text in m["id"].lower() or text in m["name"].lower()]

    def _filter_table(self, text):
        self.current_filter_text = text
        self._populate_table()

    def _show_add_dialog(self):
        dialog = MaterialDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            new_data["current_stock"] = 0 # 新物料初始库存为0
            self.materials_data.append(new_data)
            self._populate_table()
            
    def _show_edit_dialog(self, material_id):
        material_to_edit = next((m for m in self.materials_data if m["id"] == material_id), None)
        if not material_to_edit: return
        
        dialog = MaterialDialog(self, material_data=material_to_edit)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            material_to_edit.update(updated_data)
            self._populate_table()
            
    def _delete_material(self, material_id):
        reply = QMessageBox.question(self, "确认删除", f"确定要删除物料 {material_id} 吗?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.materials_data = [m for m in self.materials_data if m["id"] != material_id]
            self._populate_table()

    def _show_stock_operation_dialog(self, material_id, mode):
        """特色逻辑 2: 出入库操作"""
        material = next((m for m in self.materials_data if m["id"] == material_id), None)
        if not material: return
        
        dialog = StockOperationDialog(self, 
                                      material_name=material["name"], 
                                      current_stock=material["current_stock"], 
                                      mode=mode)
        
        if dialog.exec_() == QDialog.Accepted:
            quantity = dialog.get_quantity()
            if mode == 'in':
                material["current_stock"] += quantity
            elif mode == 'out':
                material["current_stock"] -= quantity
            
            self._populate_table() # 刷新表格，预警状态会自动更新

    def _create_mock_data(self):
        return [
            {"id": "RM-PP-001", "name": "PP-T30S 聚丙烯颗粒", "category": "原料", "current_stock": 1500, "safety_stock": 2000, "unit": "kg"},
            {"id": "RM-PE-001", "name": "HDPE-5502 聚乙烯", "category": "原料", "current_stock": 3500, "safety_stock": 2000, "unit": "kg"},
            {"id": "AD-CB-001", "name": "黑色母粒", "category": "辅料", "current_stock": 80, "safety_stock": 50, "unit": "kg"},
            {"id": "SFG-PIPE-5", "name": "5mm滴灌管半成品", "category": "半成品", "current_stock": 12500, "safety_stock": 10000, "unit": "米"},
            {"id": "PKG-ROLL-01", "name": "包装卷盘", "category": "包装材料", "current_stock": 45, "safety_stock": 100, "unit": "个"},
        ]