# pages/page_resource_coordination.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QSplitter, QGroupBox,
                             QPushButton, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from datetime import date, timedelta

class PageResourceCoordination(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- 模拟数据 ---
        self._load_mock_data()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>资源与物料协同 (MRP)</h2>"))
        header_layout.addStretch()
        run_mrp_button = QPushButton("重新运行MRP计算"); run_mrp_button.clicked.connect(self.run_mrp)
        header_layout.addWidget(run_mrp_button)
        main_layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Horizontal)
        
        mrp_panel = self._create_mrp_panel()
        inventory_panel = self._create_inventory_panel()
        
        splitter.addWidget(mrp_panel); splitter.addWidget(inventory_panel)
        main_layout.addWidget(splitter)
        
        self.run_mrp() # 初始加载时运行一次

    def _create_mrp_panel(self):
        box = QGroupBox("物料需求计划 (未来7天)")
        layout = QVBoxLayout(box)
        self.mrp_table = QTableWidget()
        self.mrp_table.cellClicked.connect(self._on_mrp_cell_clicked)
        layout.addWidget(self.mrp_table)
        return box
        
    def _create_inventory_panel(self):
        box = QGroupBox("库存状态与采购建议")
        layout = QVBoxLayout(box)
        
        self.inv_title = QLabel("请在左侧选择一个预警项"); self.inv_title.setStyleSheet("font-size: 14pt;")
        self.current_stock_label = QLabel("<b>当前库存:</b> N/A")
        self.safety_stock_label = QLabel("<b>安全库存:</b> N/A")
        self.on_order_label = QLabel("<b>在途数量:</b> N/A")
        
        self.suggestion_box = QGroupBox("采购建议"); self.suggestion_box.hide()
        sugg_layout = QVBoxLayout(self.suggestion_box)
        self.sugg_qty_label = QLabel("建议采购数量: N/A")
        self.sugg_date_label = QLabel("建议下单日期: N/A")
        self.create_po_button = QPushButton("一键生成采购申请")
        self.create_po_button.clicked.connect(self._create_purchase_order)
        sugg_layout.addWidget(self.sugg_qty_label); sugg_layout.addWidget(self.sugg_date_label); sugg_layout.addWidget(self.create_po_button)
        
        layout.addWidget(self.inv_title); layout.addWidget(self.current_stock_label)
        layout.addWidget(self.safety_stock_label); layout.addWidget(self.on_order_label)
        layout.addWidget(self.suggestion_box); layout.addStretch()
        return box

    def run_mrp(self):
        """核心特色算法：MRP 计算"""
        # 1. 获取未来7天的日期
        today = date.today()
        dates = [today + timedelta(days=i) for i in range(7)]
        
        # 2. 设置表格
        self.mrp_table.clear()
        self.mrp_table.setRowCount(len(self.db_materials))
        self.mrp_table.setColumnCount(len(dates))
        self.mrp_table.setVerticalHeaderLabels([m['name'] for m in self.db_materials])
        self.mrp_table.setHorizontalHeaderLabels([d.strftime("%m-%d") for d in dates])
        
        # 3. 按天计算物料需求
        daily_requirements = {d: {} for d in dates}
        for task in self.db_schedule:
            task_date = today + timedelta(days=task['start_day'])
            if task_date in daily_requirements:
                bom = self.db_boms.get(task['product'])
                if bom:
                    for material_id, qty_per_product in bom.items():
                        total_qty = qty_per_product * task['quantity']
                        daily_requirements[task_date][material_id] = daily_requirements[task_date].get(material_id, 0) + total_qty
        
        # 4. 计算并填充 projected_inventory，并标记短缺
        self.shortages = []
        for row, material in enumerate(self.db_materials):
            projected_inv = material['current_stock']
            for col, d in enumerate(dates):
                demand = daily_requirements[d].get(material['id'], 0)
                projected_inv -= demand
                
                item = QTableWidgetItem(f"{projected_inv:,.0f}")
                # 核心逻辑：预警判断
                if projected_inv < material['safety_stock']:
                    item.setBackground(QColor(255, 205, 210)) # 红色预警
                    self.shortages.append({'material_id': material['id'], 'date': d, 'shortage_qty': material['safety_stock'] - projected_inv})
                
                self.mrp_table.setItem(row, col, item)

    def _on_mrp_cell_clicked(self, row, column):
        material = self.db_materials[row]
        shortage_date = date.today() + timedelta(days=column)
        
        # 更新右侧面板
        self.inv_title.setText(material['name'])
        self.current_stock_label.setText(f"<b>当前库存:</b> {material['current_stock']:,.0f} {material['unit']}")
        self.safety_stock_label.setText(f"<b>安全库存:</b> {material['safety_stock']:,.0f} {material['unit']}")
        self.on_order_label.setText(f"<b>在途数量:</b> {material['on_order']:,.0f} {material['unit']}")
        
        # 检查是否有短缺，并生成建议
        is_shortage = any(s['material_id'] == material['id'] and s['date'] == shortage_date for s in self.shortages)
        if is_shortage:
            # 简化版建议：采购量 = 安全库存 + 7天总需求 - 当前库存 - 在途
            total_demand_7d = sum(daily_req.get(material['id'], 0) for daily_req in self.run_mrp_for_demand_calc().values())
            purchase_qty = material['safety_stock'] + total_demand_7d - material['current_stock'] - material['on_order']
            purchase_qty = max(0, purchase_qty) # 确保不为负
            
            # 建议下单日期 = 短缺日期 - 采购提前期
            order_date = shortage_date - timedelta(days=material['lead_time'])
            
            self.sugg_qty_label.setText(f"建议采购数量: {purchase_qty:,.0f} {material['unit']}")
            self.sugg_date_label.setText(f"建议下单日期: {order_date.strftime('%Y-%m-%d')}")
            self.create_po_button.setProperty("material_id", material['id']) # 存储ID以备后用
            self.create_po_button.setProperty("purchase_qty", purchase_qty)
            self.suggestion_box.show()
        else:
            self.suggestion_box.hide()

    def _create_purchase_order(self):
        material_id = self.sender().property("material_id")
        qty = self.sender().property("purchase_qty")
        
        material = next((m for m in self.db_materials if m['id'] == material_id), None)
        if not material: return
        
        reply = QMessageBox.question(self, "确认生成采购申请", f"为物料 {material['name']} 生成一张数量为 {qty:,.0f} {material['unit']} 的采购申请单吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            material['on_order'] += qty
            QMessageBox.information(self, "成功", "采购申请已生成！\n物料的在途数量已更新。")
            self._on_mrp_cell_clicked(self.mrp_table.currentRow(), self.mrp_table.currentColumn()) # 刷新右侧面板

    def run_mrp_for_demand_calc(self): # Helper for calculation
        today = date.today(); dates = [today + timedelta(days=i) for i in range(7)]
        daily_requirements = {d: {} for d in dates}
        for task in self.db_schedule:
            task_date = today + timedelta(days=task['start_day'])
            if task_date in daily_requirements:
                bom = self.db_boms.get(task['product'])
                if bom:
                    for mat_id, qty_pp in bom.items():
                        daily_requirements[task_date][mat_id] = daily_requirements[task_date].get(mat_id, 0) + qty_pp * task['quantity']
        return daily_requirements

    def _load_mock_data(self):
        # 模拟生产排程 (未来1-2周)
        self.db_schedule = [
            {'product': '5mm_pipe', 'quantity': 10000, 'start_day': 1},
            {'product': '8mm_pipe', 'quantity': 8000, 'start_day': 2},
            {'product': '5mm_pipe', 'quantity': 15000, 'start_day': 4},
            {'product': '8mm_pipe', 'quantity': 12000, 'start_day': 6},
        ]
        # 模拟物料清单 (BOM)
        self.db_boms = {
            '5mm_pipe': {'RM-PP-001': 0.02, 'AD-CB-001': 0.001}, # kg/米
            '8mm_pipe': {'RM-PE-001': 0.03, 'AD-CB-001': 0.001},
        }
        # 模拟物料主数据/库存
        self.db_materials = [
            {'id': 'RM-PP-001', 'name': 'PP颗粒', 'current_stock': 500, 'safety_stock': 300, 'on_order': 0, 'unit': 'kg', 'lead_time': 5},
            {'id': 'RM-PE-001', 'name': 'PE颗粒', 'current_stock': 800, 'safety_stock': 400, 'on_order': 500, 'unit': 'kg', 'lead_time': 7},
            {'id': 'AD-CB-001', 'name': '黑色母粒', 'current_stock': 50, 'safety_stock': 20, 'on_order': 0, 'unit': 'kg', 'lead_time': 3},
        ]