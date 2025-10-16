# pages/page_quality.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFrame, QTreeWidget, QTreeWidgetItem,
                             QSplitter, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import random

class PageQuality(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. 模拟一个关系型数据库
        self._create_mock_database()

        # UI 布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        search_widget = self._create_search_widget()
        main_layout.addWidget(search_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.trace_tree = QTreeWidget()
        self.trace_tree.setHeaderLabels(["追溯项目", "关键信息"])
        self.trace_tree.header().setSectionResizeMode(0, pg.QtWidgets.QHeaderView.ResizeToContents)
        self.trace_tree.itemClicked.connect(self._on_tree_item_clicked)
        
        self.details_panel = QFrame()
        self.details_layout = QVBoxLayout(self.details_panel)
        # --- 修改：设置一个更好看的初始占位符 ---
        initial_label = QLabel("输入产品批次号开始追溯，或查看默认案例。")
        initial_label.setAlignment(Qt.AlignCenter)
        initial_label.setStyleSheet("color: #B0BEC5; font-size: 14pt;")
        self.details_layout.addWidget(initial_label)

        splitter.addWidget(self.trace_tree)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        
        main_layout.addWidget(splitter)
        
        # --- 2. 新增：页面加载时自动执行一次追溯 ---
        self._load_default_trace()

    def _create_search_widget(self):
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(widget)
        
        layout.addWidget(QLabel("输入产品批次号:"))
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("例如: PROD-20231028-001")
        search_button = QPushButton("开始追溯")
        search_button.clicked.connect(self._start_trace)
        
        layout.addWidget(self.batch_input)
        layout.addWidget(search_button)
        return widget

    def _load_default_trace(self):
        """新增方法：加载并显示默认的追溯案例"""
        default_batch_id = "PROD-20231028-001"
        self.batch_input.setText(default_batch_id) # 将默认批次号填入输入框
        self._start_trace() # 调用追溯方法

    def _start_trace(self):
        batch_id = self.batch_input.text()
        if not batch_id:
            return
            
        self.trace_tree.clear()
        
        product_batch_info = self.db_product_batches.get(batch_id)
        if not product_batch_info:
            root_item = QTreeWidgetItem(self.trace_tree, ["错误", "未找到该产品批次"])
            return

        root_item = QTreeWidgetItem(self.trace_tree, [f"产品批次: {batch_id}", product_batch_info['product_name']])
        root_item.setData(0, Qt.UserRole, {'type': 'product_batch', 'id': batch_id})
        
        wo_id = product_batch_info['work_order_id']
        wo_info = self.db_work_orders.get(wo_id)
        if wo_info:
            wo_item = QTreeWidgetItem(root_item, ["生产工单", wo_id])
            wo_item.setData(0, Qt.UserRole, {'type': 'work_order', 'id': wo_id})
            
            device_id = wo_info['device_id']
            device_item = QTreeWidgetItem(wo_item, ["生产设备", device_id])
            device_item.setData(0, Qt.UserRole, {'type': 'device', 'id': device_id, 'timestamp': product_batch_info['production_time']})
            
            for material_batch_id in wo_info['material_batches']:
                material_item = QTreeWidgetItem(wo_item, ["使用原料", material_batch_id])
                material_item.setData(0, Qt.UserRole, {'type': 'material_batch', 'id': material_batch_id})
                QTreeWidgetItem(material_item, ["点击展开更多..."])

        qc_id = product_batch_info['qc_record_id']
        qc_info = self.db_qc_records.get(qc_id)
        if qc_info:
            qc_item = QTreeWidgetItem(root_item, ["质检记录", qc_id])
            qc_item.setData(0, Qt.UserRole, {'type': 'qc_record', 'id': qc_id})

        root_item.setExpanded(True)
        
        # --- 3. 新增：自动选中根节点以显示其详情 ---
        self.trace_tree.setCurrentItem(root_item)
        self._update_details_panel(root_item.data(0, Qt.UserRole))


    def _on_tree_item_clicked(self, item, column):
        node_data = item.data(0, Qt.UserRole)
        if not node_data:
            return

        if "点击展开更多..." in item.text(0) and node_data['type'] == 'material_batch':
            parent_item = item.parent()
            parent_item.removeChild(item)
            material_info = self.db_material_batches.get(node_data['id'])
            if material_info:
                supplier_item = QTreeWidgetItem(parent_item, ["供应商", material_info['supplier']])
                supplier_item.setData(0, Qt.UserRole, {'type': 'supplier', 'id': material_info['supplier']})
        
        self._update_details_panel(node_data)
        
    def _update_details_panel(self, node_data):
        for i in reversed(range(self.details_layout.count())): 
            widget = self.details_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        node_type = node_data['type']
        node_id = node_data['id']
        
        title_text = f"详情: {node_type.replace('_', ' ').title()} - {node_id}"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding-bottom: 10px;")
        self.details_layout.addWidget(title)

        if node_type == 'product_batch':
            info = self.db_product_batches[node_id]
            text = f"产品名称: {info['product_name']}\n" \
                   f"生产时间: {info['production_time']}\n" \
                   f"关联工单: {info['work_order_id']}"
            self.details_layout.addWidget(QTextEdit(text))
            
        elif node_type == 'device':
            graph_box = QGroupBox("生产时段关键参数")
            graph_layout = QVBoxLayout()
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('#263238')
            plot_widget.setTitle(f"设备 {node_id} 在 {node_data['timestamp']} 附近的参数", color="#B0BEC5")
            plot_widget.plot(self._get_mock_sensor_data(), pen='r', name='温度')
            plot_widget.plot(self._get_mock_sensor_data(base=2.0, var=0.2), pen='g', name='压力')
            plot_widget.addLegend()
            graph_layout.addWidget(plot_widget)
            graph_box.setLayout(graph_layout)
            self.details_layout.addWidget(graph_box)

        elif node_type == 'qc_record':
            info = self.db_qc_records[node_id]
            text = f"质检员: {info['inspector']}\n" \
                   f"质检时间: {info['time']}\n" \
                   f"结果: {info['result']}\n\n" \
                   f"详细记录:\n{info['details']}"
            self.details_layout.addWidget(QTextEdit(text))
            
        else:
             self.details_layout.addWidget(QTextEdit(f"关于 {node_id} 的详细信息...\n"
                                                      f"类型: {node_type}"))

        self.details_layout.addStretch()
        
    def _create_mock_database(self):
        self.db_product_batches = { "PROD-20231028-001": {"product_name": "5mm 滴灌管 (黑色)", "production_time": "2023-10-28 14:30", "work_order_id": "WO-20231028-001", "qc_record_id": "QC-20231028-001"} }
        self.db_work_orders = { "WO-20231028-001": {"device_id": "EXTRUDER-A", "material_batches": ["RM-PP-001-B789", "AD-CB-001-B112"]} }
        self.db_material_batches = { "RM-PP-001-B789": {"supplier": "巴斯夫化工", "inbound_date": "2023-10-15"}, "AD-CB-001-B112": {"supplier": "陶氏化学", "inbound_date": "2023-10-12"}, }
        self.db_qc_records = { "QC-20231028-001": {"inspector": "张三", "time": "2023-10-28 16:00", "result": "合格", "details": "外观检测: OK\n尺寸检测: OK\n耐压测试: OK"} }

    def _get_mock_sensor_data(self, base=85, var=2):
        return [base + random.uniform(-var, var) for _ in range(20)]