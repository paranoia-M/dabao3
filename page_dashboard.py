# pages/page_dashboard.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QGroupBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
import pyqtgraph as pg

from device_simulator import SchedulingSimulatorThread

class KPICard(QGroupBox):
    """一个显示核心指标的卡片"""
    def __init__(self, title):
        super().__init__(title)
        layout = QVBoxLayout(self)
        self.value_label = QLabel("0.0%"); self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 28pt; font-weight: bold;")
        layout.addWidget(self.value_label)

class DonutChart(pg.GraphicsObject):
    """自定义环形图"""
    def __init__(self, percentage=0):
        super().__init__()
        self.percentage = percentage
    
    def set_percentage(self, p):
        self.percentage = p
        self.update()

    def paint(self, p, *args):
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.boundingRect()
        
        # Draw background circle
        p.setPen(QPen(QColor(60, 60, 60), 20))
        p.drawEllipse(rect.center(), rect.width()/2 - 10, rect.width()/2 - 10)
        
        # Draw foreground arc
        if self.percentage > 0:
            p.setPen(QPen(QColor("#00C853"), 20))
            p.drawArc(rect, 90 * 16, -int(self.percentage * 360 * 16))
            
        # Draw text
        font = QFont(); font.setPointSize(18); font.setBold(True)
        p.setFont(font); p.setPen(QColor("white"))
        p.drawText(rect, Qt.AlignCenter, f"{self.percentage*100:.1f}%")

    def boundingRect(self):
        return pg.QtCore.QRectF(-100, -100, 200, 200)

class PageDashboard(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QGridLayout(self); main_layout.setSpacing(20)
        
        kpi_panel = self._create_kpi_panel()
        progress_panel = self._create_progress_panel()
        status_panel = self._create_status_panel()
        diagnosis_panel = self._create_diagnosis_panel()
        
        main_layout.addLayout(kpi_panel, 0, 0, 1, 3)
        main_layout.addWidget(progress_panel, 1, 0)
        main_layout.addWidget(status_panel, 1, 1)
        main_layout.addWidget(diagnosis_panel, 1, 2)
        
        main_layout.setColumnStretch(0, 1); main_layout.setColumnStretch(1, 2); main_layout.setColumnStretch(2, 1)

        self.simulator = SchedulingSimulatorThread(self)
        self.simulator.data_updated.connect(self.update_ui)
        self.simulator.start()

    def _create_kpi_panel(self):
        layout = QHBoxLayout()
        self.kpis = {
            'order': KPICard("订单完成率"), 'plan': KPICard("计划达成率"),
            'oee': KPICard("设备综合效率 (OEE)"), 'quality': KPICard("在线合格率")
        }
        for card in self.kpis.values(): layout.addWidget(card)
        return layout
        
    def _create_progress_panel(self):
        box = QGroupBox("今日生产总进度")
        layout = QVBoxLayout(box)
        
        self.donut_chart = DonutChart()
        view = pg.GraphicsView(); view.setBackground(None)
        scene = pg.GraphicsScene(); scene.addItem(self.donut_chart)
        view.setScene(scene); view.fitInView(self.donut_chart.boundingRect(), Qt.KeepAspectRatio)
        
        self.progress_label = QLabel("0 / 0 米")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(view); layout.addWidget(self.progress_label)
        return box
        
    def _create_status_panel(self):
        box = QGroupBox("核心设备状态矩阵")
        self.status_layout = QGridLayout(box)
        self.device_labels = {}
        return box
        
    def _create_diagnosis_panel(self):
        box = QGroupBox("智能诊断与建议")
        layout = QVBoxLayout(box)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("<b>当前主要瓶颈:</b>"))
        self.bottleneck_label = QLabel("分析中..."); self.bottleneck_label.setStyleSheet("color: #FFC107; font-size: 14pt;")
        self.bottleneck_label.setWordWrap(True)
        
        layout.addWidget(QLabel("<b>改进建议:</b>"))
        self.suggestion_label = QLabel("请等待系统分析..."); self.suggestion_label.setWordWrap(True)
        
        layout.addWidget(self.bottleneck_label); layout.addStretch(); layout.addWidget(self.suggestion_label); layout.addStretch(2)
        return box

    def update_ui(self, data):
        # 1. 更新KPI卡片
        self.kpis['order'].value_label.setText(f"{data['order_completion_rate']:.1%}")
        self.kpis['plan'].value_label.setText(f"{data['plan_achievement_rate']:.1%}")
        self.kpis['oee'].value_label.setText(f"{data['oee']:.1f}%")
        self.kpis['quality'].value_label.setText(f"{data['quality_rate']:.1f}%")
        
        # 2. 更新环形图
        self.donut_chart.set_percentage(data['plan_achievement_rate'])
        self.progress_label.setText(f"{int(data['current_output'])} / {data['plan_output']} 米")

        # 3. 更新设备状态矩阵
        self._update_device_status(data['devices_status'])

        # 4. 运行核心算法：瓶颈诊断
        self._diagnose_bottleneck(data)
        
    def _update_device_status(self, statuses):
        status_colors = {'running': "#4CAF50", 'idle': "#FFC107", 'fault': "#D32F2F"}
        if not self.device_labels: # 第一次运行时创建标签
             for i, (name, status) in enumerate(statuses.items()):
                label = QLabel(name); label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("padding: 10px; border-radius: 5px;")
                self.device_labels[name] = label
                self.status_layout.addWidget(label, i // 2, i % 2)

        for name, label in self.device_labels.items():
            status = statuses.get(name, 'unknown')
            label.setStyleSheet(f"background-color: {status_colors.get(status, 'gray')}; padding: 10px; border-radius: 5px;")

    def _diagnose_bottleneck(self, data):
        """核心特色算法: 生产瓶颈诊断专家系统"""
        bottleneck = "暂无明显瓶颈"
        suggestion = "继续保持当前生产状态，密切监控各项指标。"
        
        # 规则1: OEE是主要问题
        if data['oee'] < 75 and data['plan_achievement_rate'] < 0.9:
            bottleneck = "设备综合效率 (OEE) 低"
            suggestion = "请立即检查设备状态矩阵，定位故障或待机设备。建议调度维修人员，并分析设备停机原因，优化维护计划。"
        
        # 规则2: 质量是主要问题
        elif data['quality_rate'] < 98.0:
            bottleneck = "产品质量不稳定"
            suggestion = "请转到'在线质量视觉'和'工艺参数深潜'页面，追溯近期次品产生时段的工艺参数，找出根本原因。建议加强对原料和操作流程的巡检。"

        # 规则3: 计划本身可能存在问题
        elif data['plan_achievement_rate'] < 0.85 and data['oee'] > 85:
            bottleneck = "计划达成率低，但设备效率正常"
            suggestion = "瓶颈可能在于上游的'排程'或'物料'环节。请检查'安全排程管理'是否排程过于紧张，或'安全信息管理'页面是否存在物料短缺预警。"
        
        self.bottleneck_label.setText(bottleneck)
        self.suggestion_label.setText(suggestion)
        
    def closeEvent(self, event):
        self.simulator.stop()
        super().closeEvent(event)