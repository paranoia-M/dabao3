# pages/page_reports.py
import csv
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QTabWidget, QDateEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFileDialog, QGroupBox)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
import pyqtgraph as pg

# 自定义饼图项
class PieChartItem(pg.GraphicsObject):
    def __init__(self, data):
        super().__init__()
        self.data = data # data is a list of (value, color) tuples
        self.generatePicture()

    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        p = QPainter(self.picture)
        total = sum(d[0] for d in self.data)
        if total == 0: return
        
        start_angle = 0
        for value, color in self.data:
            angle = value / total * 360 * 16
            p.setBrush(QBrush(color))
            p.setPen(QPen(Qt.black))
            p.drawPie(self.boundingRect(), int(start_angle), int(angle))
            start_angle += angle
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(-50, -50, 100, 100)

class PageReports(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- 数据 ---
        self.full_production_data = self._create_mock_data(days=30)
        self.filtered_data = []

        # --- UI 布局 ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        filters_widget = self._create_filters_widget()
        main_layout.addWidget(filters_widget)

        self.tabs = QTabWidget()
        self.prod_summary_tab = QWidget()
        self.oee_analysis_tab = QWidget()
        self.tabs.addTab(self.prod_summary_tab, "生产综合报表")
        self.tabs.addTab(self.oee_analysis_tab, "设备综合效率(OEE)分析")
        
        main_layout.addWidget(self.tabs)
        
        # 为每个Tab页设置布局
        self._setup_production_summary_tab()
        self._setup_oee_analysis_tab()
        
    def _create_filters_widget(self):
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(widget)

        layout.addWidget(QLabel("日期范围:"))
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit.setCalendarPopup(True)
        
        generate_button = QPushButton("生成报表")
        generate_button.clicked.connect(self._generate_reports)
        
        export_button = QPushButton("导出为CSV")
        export_button.clicked.connect(self._export_to_csv)

        layout.addWidget(self.start_date_edit)
        layout.addWidget(QLabel("至"))
        layout.addWidget(self.end_date_edit)
        layout.addWidget(generate_button)
        layout.addStretch()
        layout.addWidget(export_button)
        return widget

    def _setup_production_summary_tab(self):
        layout = QHBoxLayout(self.prod_summary_tab)
        
        # 左侧表格
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(4)
        self.prod_table.setHorizontalHeaderLabels(["日期", "计划产量(米)", "实际产量(米)", "合格率(%)"])
        
        # 右侧图表
        charts_layout = QVBoxLayout()
        self.bar_chart = pg.PlotWidget()
        self.pie_chart_view = pg.GraphicsView()
        self.pie_chart_view.setBackground(None) # 透明背景
        charts_layout.addWidget(QLabel("每日产量对比"))
        charts_layout.addWidget(self.bar_chart)
        charts_layout.addWidget(QLabel("各产品产量分布"))
        charts_layout.addWidget(self.pie_chart_view)
        
        layout.addWidget(self.prod_table, 2) # 表格占2份
        layout.addLayout(charts_layout, 1) # 图表占1份
        
    def _setup_oee_analysis_tab(self):
        layout = QVBoxLayout(self.oee_analysis_tab)
        
        # 顶部指标卡片
        kpi_layout = QHBoxLayout()
        self.oee_score_label = self._create_kpi_card("OEE 总分", "N/A")
        self.availability_label = self._create_kpi_card("可用率", "N/A")
        self.performance_label = self._create_kpi_card("性能", "N/A")
        self.quality_label = self._create_kpi_card("质量", "N/A")
        kpi_layout.addWidget(self.oee_score_label)
        kpi_layout.addWidget(self.availability_label)
        kpi_layout.addWidget(self.performance_label)
        kpi_layout.addWidget(self.quality_label)
        
        # 底部原始数据表格
        self.oee_table = QTableWidget()
        self.oee_table.setColumnCount(6)
        self.oee_table.setHorizontalHeaderLabels(["日期", "计划运行(h)", "故障停机(h)", "实际产量", "理论产量", "合格品数"])
        
        layout.addLayout(kpi_layout)
        layout.addWidget(self.oee_table)
        
    def _create_kpi_card(self, title, value):
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        label = QLabel(value)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 28pt; font-weight: bold;")
        box_layout.addWidget(label)
        return box

    def _generate_reports(self):
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        self.filtered_data = [d for d in self.full_production_data if start_date <= d['date'] <= end_date]
        
        if not self.filtered_data:
            print("该日期范围内没有数据。")
            return
            
        self._update_production_summary()
        self._update_oee_analysis()

    def _update_production_summary(self):
        # 按日期聚合数据
        summary = {}
        for record in self.filtered_data:
            date_str = record['date'].strftime("%Y-%m-%d")
            if date_str not in summary:
                summary[date_str] = {'plan': 0, 'actual': 0, 'qualified': 0}
            summary[date_str]['plan'] += record['plan_output']
            summary[date_str]['actual'] += record['actual_output']
            summary[date_str]['qualified'] += record['actual_output'] - record['defects']
            
        # 填充表格
        self.prod_table.setRowCount(len(summary))
        sorted_dates = sorted(summary.keys())
        for row, date_str in enumerate(sorted_dates):
            data = summary[date_str]
            quality_rate = (data['qualified'] / data['actual'] * 100) if data['actual'] > 0 else 0
            self.prod_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.prod_table.setItem(row, 1, QTableWidgetItem(str(data['plan'])))
            self.prod_table.setItem(row, 2, QTableWidgetItem(str(data['actual'])))
            self.prod_table.setItem(row, 3, QTableWidgetItem(f"{quality_rate:.2f}"))
            
        # 更新条形图
        self.bar_chart.clear()
        ticks = [(i, date) for i, date in enumerate(sorted_dates)]
        self.bar_chart.getAxis('bottom').setTicks([ticks])
        bar_item = pg.BarGraphItem(x=range(len(summary)), height=[summary[d]['actual'] for d in sorted_dates], width=0.6)
        self.bar_chart.addItem(bar_item)
        
        # 更新饼图
        product_summary = {}
        for record in self.filtered_data:
            product = record['product']
            product_summary[product] = product_summary.get(product, 0) + record['actual_output']
        
        colors = [QColor("#00BCD4"), QColor("#FFC107"), QColor("#8BC34A"), QColor("#D32F2F")]
        pie_data = [(v, colors[i % len(colors)]) for i, v in enumerate(product_summary.values())]
        pie = PieChartItem(pie_data)
        scene = pg.QtWidgets.QGraphicsScene()
        scene.addItem(pie)
        self.pie_chart_view.setScene(scene)
        self.pie_chart_view.fitInView(pie.boundingRect(), Qt.KeepAspectRatio)
        
    def _update_oee_analysis(self):
        # --- 特色逻辑：OEE计算 ---
        oee_results = self._calculate_oee(self.filtered_data)
        
        # 更新KPI卡片
        self.oee_score_label.findChild(QLabel).setText(f"{oee_results['oee']:.1%}")
        self.availability_label.findChild(QLabel).setText(f"{oee_results['availability']:.1%}")
        self.performance_label.findChild(QLabel).setText(f"{oee_results['performance']:.1%}")
        self.quality_label.findChild(QLabel).setText(f"{oee_results['quality']:.1%}")
        
        # 填充原始数据表格
        self.oee_table.setRowCount(len(self.filtered_data))
        for row, record in enumerate(self.filtered_data):
            self.oee_table.setItem(row, 0, QTableWidgetItem(record['date'].strftime("%Y-%m-%d")))
            self.oee_table.setItem(row, 1, QTableWidgetItem(str(8.0))) # 假设每天8小时
            self.oee_table.setItem(row, 2, QTableWidgetItem(str(record['downtime_hours'])))
            self.oee_table.setItem(row, 3, QTableWidgetItem(str(record['actual_output'])))
            self.oee_table.setItem(row, 4, QTableWidgetItem(str(record['plan_output'])))
            self.oee_table.setItem(row, 5, QTableWidgetItem(str(record['actual_output'] - record['defects'])))
            
    def _calculate_oee(self, data):
        total_planned_time = len(set(d['date'] for d in data)) * 8.0 # 每天8小时
        total_downtime = sum(d['downtime_hours'] for d in data)
        actual_run_time = total_planned_time - total_downtime
        
        total_actual_output = sum(d['actual_output'] for d in data)
        total_plan_output = sum(d['plan_output'] for d in data)
        total_defects = sum(d['defects'] for d in data)
        
        availability = actual_run_time / total_planned_time if total_planned_time > 0 else 0
        performance = total_actual_output / total_plan_output if total_plan_output > 0 else 0
        quality = (total_actual_output - total_defects) / total_actual_output if total_actual_output > 0 else 0
        
        oee = availability * performance * quality
        return {
            "oee": oee, "availability": availability, 
            "performance": performance, "quality": quality
        }
        
    def _export_to_csv(self):
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == 0:
            table = self.prod_table
            default_filename = "production_summary.csv"
        elif current_tab_index == 1:
            table = self.oee_table
            default_filename = "oee_analysis_data.csv"
        else:
            return

        path, _ = QFileDialog.getSaveFileName(self, "保存文件", default_filename, "CSV Files (*.csv)")
        
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
                writer = csv.writer(stream)
                # 写入表头
                headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
                writer.writerow(headers)
                # 写入数据
                for row in range(table.rowCount()):
                    row_data = [table.item(row, col).text() for col in range(table.columnCount())]
                    writer.writerow(row_data)

    def _create_mock_data(self, days=30):
        data = []
        products = ["5mm 滴灌管", "8mm 滴灌管", "12mm PE管"]
        today = datetime.now().date()
        for i in range(days):
            current_date = today - timedelta(days=i)
            for _ in range(random.randint(2, 4)): # 每天有多条记录
                plan = random.randint(3000, 5000)
                actual = int(plan * random.uniform(0.85, 0.98))
                data.append({
                    "date": current_date,
                    "product": random.choice(products),
                    "plan_output": plan,
                    "actual_output": actual,
                    "defects": int(actual * random.uniform(0.01, 0.05)),
                    "downtime_hours": round(random.uniform(0.1, 1.0), 2)
                })
        return data