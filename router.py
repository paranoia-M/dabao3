# router.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

# --- 导入所有实际存在的页面类 ---
from pages.page_dashboard import PageDashboard 
from pages.page_order_pool import PageOrderPool
from pages.page_scheduling_workbench import PageSchedulingWorkbench
from pages.page_mes_cockpit import PageMesCockpit
from pages.page_resource_coordination import PageResourceCoordination
from pages.page_quality_traceability import PageQualityTraceability
from pages.page_performance_kpi import PagePerformanceKpi # <-- 新增导入

def create_placeholder_page(text):
    """一个辅助函数，用于快速创建占位符页面"""
    page = QWidget()
    layout = QVBoxLayout(page)
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("font-size: 24pt; color: #78909C;")
    layout.addWidget(label)
    return page

def get_page_widget(page_key):
    """
    根据 page_key 返回对应的页面实例。
    这个函数是路由的核心。
    """
    if page_key == "dashboard": 
        return PageDashboard()
    
    if page_key == "order_pool": 
        return PageOrderPool()
        
    if page_key == "scheduling_workbench": 
        return PageSchedulingWorkbench()
        
    if page_key == "mes_cockpit": 
        return PageMesCockpit()
        
    if page_key == "resource_coordination": 
        return PageResourceCoordination()
        
    if page_key == "quality_traceability": 
        return PageQualityTraceability()
        
    if page_key == "performance_kpi": 
        return PagePerformanceKpi() # <-- 新增路由
        
    # 如果传入一个未知的 key，返回一个错误提示页面
    return create_placeholder_page(f"错误: 页面 '{page_key}' 未定义")