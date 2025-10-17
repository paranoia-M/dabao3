# main_window.py

from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QAction
from PyQt5.QtCore import Qt

import user_manager
from widgets.side_menu import SideMenu
import router # 使用路由分离

class MainWindow(QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("网络数据信息安全防火墙配置管理系统")

        self.logout_triggered = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.side_menu = SideMenu()
        self.stacked_widget = QStackedWidget()
        
        main_layout.addWidget(self.side_menu)
        main_layout.addWidget(self.stacked_widget)
        
        self.pages = {}

        self.init_ui()
        self._create_actions_menu()

    def init_ui(self):
        self.side_menu.page_changed.connect(self.switch_page)
        self.populate_menu()
        self.statusBar().showMessage(f"欢迎您，{self.username}！")
        self.switch_page("dashboard")
        self.side_menu.set_current_item_by_key("dashboard")

    def populate_menu(self):
        """向侧边栏添加所有新主题的菜单项"""
        self.side_menu.add_menu_item("系统总览", "dashboard")
        self.side_menu.add_menu_item("安全订单需求", "order_pool")
        self.side_menu.add_menu_item("安全排程管理", "scheduling_workbench")
        self.side_menu.add_menu_item("生产执行监控", "mes_cockpit")
        self.side_menu.add_menu_item("安全信息管理", "resource_coordination")
        self.side_menu.add_menu_item("质量与工艺追溯", "quality_traceability")
        self.side_menu.add_menu_item("绩效分析与KPI", "performance_kpi")

    def switch_page(self, page_key):
        if page_key not in self.pages:
            widget = router.get_page_widget(page_key)
            self.stacked_widget.addWidget(widget)
            self.pages[page_key] = widget

        widget_to_show = self.pages[page_key]
        self.stacked_widget.setCurrentWidget(widget_to_show)
        
        current_item = self.side_menu.list_widget.currentItem()
        if current_item:
            self.statusBar().showMessage(f"当前页面: {current_item.text()}")

    def _create_actions_menu(self):
        menu_bar = self.menuBar()
        user_menu = menu_bar.addMenu(f"用户: {self.username}")
        logout_action = QAction("登出", self)
        logout_action.triggered.connect(self._handle_logout)
        user_menu.addAction(logout_action)

    def _handle_logout(self):
        user_manager.logout_user()
        self.logout_triggered = True
        self.close()