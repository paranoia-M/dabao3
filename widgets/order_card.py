# widgets/order_card.py
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QContextMenuEvent

class OrderCard(QFrame):
    # --- 新增：定义一个自定义信号，在需要显示菜单时发出 ---
    request_context_menu = pyqtSignal(object, QContextMenuEvent) # (order_id, event)

    def __init__(self, order_data):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.order_data = order_data
        
        main_layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        id_label = QLabel(f"<b>{order_data['id']}</b>")
        self.score_label = QLabel(f"优先级: {order_data.get('priority', 0)}")
        header_layout.addWidget(id_label); header_layout.addStretch(); header_layout.addWidget(self.score_label)
        
        prod_label = QLabel(order_data['product']); qty_label = QLabel(f"数量: {order_data['quantity']:,} 米")
        due_date_label = QLabel(f"交期: {order_data['due_date'].strftime('%Y-%m-%d')}")
        
        main_layout.addLayout(header_layout); main_layout.addWidget(prod_label); main_layout.addWidget(qty_label); main_layout.addWidget(due_date_label)
        
        self.update_color()

    def update_color(self):
        score = self.order_data.get('priority', 0)
        if score > 80: color = QColor(255, 205, 210)
        elif score > 60: color = QColor(255, 224, 178)
        else: color = QColor(238, 238, 238)
        self.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #BDBDBD; border-radius: 5px; padding: 8px;")

    # --- 新增：重写右键菜单事件 ---
    def contextMenuEvent(self, event: QContextMenuEvent):
        """当用户右键点击卡片时，发出信号"""
        self.request_context_menu.emit(self.order_data['id'], event)