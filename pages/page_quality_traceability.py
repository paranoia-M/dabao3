# pages/page_quality_traceability.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTextEdit, QGroupBox, QDialog)
import pyqtgraph as pg
import numpy as np

from .widgets.fishbone_diagram import FishboneDiagram

class PageQualityTraceability(QWidget):
    def __init__(self):
        super().__init__()
        self._create_mock_db()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        search_panel = self._create_search_panel()
        self.fishbone_diagram = FishboneDiagram()
        self.details_panel = QTextEdit("可以在鱼骨图上的节点可查看详细信息..."); 
        self.details_panel.setReadOnly(True); self.details_panel.setMaximumHeight(120)

        main_layout.addWidget(search_panel)
        main_layout.addWidget(self.fishbone_diagram)
        main_layout.addWidget(self.details_panel)
        main_layout.setStretch(1, 1)
        
        self._run_traceability()
        
    def _create_search_panel(self):
        panel = QGroupBox("追溯入口")
        layout = QHBoxLayout(panel)
        layout.addWidget(QLabel("输入产品批次号:")); self.batch_input = QLineEdit("PROD-BATCH-003")
        trace_button = QPushButton("根本原因分析"); trace_button.clicked.connect(self._run_traceability)
        layout.addWidget(self.batch_input); layout.addWidget(trace_button); layout.addStretch()
        return panel

    def _run_traceability(self):
        batch_id = self.batch_input.text()
        batch_info = self.db_batches.get(batch_id)
        if not batch_info: self.details_panel.setText(f"错误：找不到批次号 {batch_id}"); return
        causes = self._find_potential_causes(batch_info['wo_id'])
        self.fishbone_diagram.draw(batch_info['quality_issue'], causes, self._on_node_clicked)

    def _on_node_clicked(self, node_data):
        """核心交互 3: 节点点击后的处理函数"""
        details = node_data.get('details', {})
        
        # 更新下方面板的文本信息
        text_info = f"<h3>{node_data['label']}</h3>"
        for key, value in details.items():
            if key != 'historical_data': # 不显示原始数据
                text_info += f"<b>{key}:</b> {value}<br>"
        self.details_panel.setHtml(text_info)
        
        # --- 特色交互：如果点击的是工艺参数，弹出历史数据图表 ---
        if node_data.get('type') == 'method':
            self.show_parameter_chart(node_data['label'], details['historical_data'])

    def show_parameter_chart(self, title, data):
        """弹出一个新窗口显示历史数据图表"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"历史数据: {title}")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        plot = pg.PlotWidget()
        plot.setBackground(None)
        plot.plot(data['values'], pen='b')
        plot.setTitle(title)
        
        # 高亮显示异常区域
        if 'anomaly_range' in data:
            lr = pg.LinearRegionItem(values=data['anomaly_range'], brush=(255, 0, 0, 50), movable=False)
            plot.addItem(lr)
            
        layout.addWidget(plot)

    def _find_potential_causes(self, wo_id):
        wo_info = self.db_work_orders[wo_id]
        causes = {'人': [], '机': [], '料': [], '法': []}

        op = self.db_operators[wo_info['operator_id']]
        causes['人'].append({'label': op['name'], 'type': 'man', 'suspicion': 'low' if op['experience'] < 1 else 'none',
                             'details': {'姓名': op['name'], '工龄(年)': op['experience']}})
        
        dev = self.db_devices[wo_info['device_id']]
        causes['机'].append({'label': dev['name'], 'type': 'machine', 'suspicion': 'medium' if dev['maintenance_overdue'] else 'none',
                             'details': {'设备名称': dev['name'], '保养是否逾期': dev['maintenance_overdue']}})
        
        mat = self.db_materials[wo_info['material_batch_id']]
        causes['料'].append({'label': mat['id'], 'type': 'material', 'suspicion': 'none',
                             'details': {'批次号': mat['id'], '供应商': mat['supplier']}})
        
        params = self.db_process_params[wo_info['params_id']]
        is_temp_bad = not (85 < params['temp_avg'] < 95)
        causes['法'].append({'label': f"温度: {params['temp_avg']}°C", 'type': 'method', 'suspicion': 'high' if is_temp_bad else 'none',
                             'details': {'参数': '温度', '平均值': f"{params['temp_avg']}°C", '设定范围': '85-95°C', 'historical_data': params['temp_data']}})
        return causes

    def _create_mock_db(self):
        self.db_batches = {"PROD-BATCH-003": {"quality_issue": "表面划痕", "wo_id": "WO-007"}}
        self.db_work_orders = {"WO-007": {"operator_id": "OP-02", "device_id": "EXT-A", "material_batch_id": "MAT-PP-B88", "params_id": "P-102"}}
        self.db_operators = {"OP-01": {"name": "张工", "experience": 5}, "OP-02": {"name": "李新", "experience": 0.5}}
        self.db_devices = {"EXT-A": {"name": "挤出机A", "maintenance_overdue": True}, "EXT-B": {"name": "挤出机B", "maintenance_overdue": False}}
        self.db_materials = {"MAT-PP-B88": {"id": "MAT-PP-B88", "supplier": "巴斯夫"}}
        
        # 模拟包含异常的详细历史数据
        temp_history = 90 + np.random.randn(100) * 0.5
        temp_history[40:60] = 98 + np.random.randn(20) * 0.5 # 制造一段异常高温
        self.db_process_params = {
            "P-101": {"temp_avg": 90, "speed_avg": 50},
            "P-102": {"temp_avg": np.mean(temp_history), "speed_avg": 52, 
                      "temp_data": {'values': temp_history, 'anomaly_range': (40, 60)}}
        }