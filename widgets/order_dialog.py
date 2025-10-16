# widgets/order_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QDateEdit, QComboBox, QDialogButtonBox)
from PyQt5.QtCore import QDate
import datetime

class OrderDialog(QDialog):
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent); self.setWindowTitle("订单信息")
        
        self.order_id = QLineEdit(); self.product_name = QLineEdit()
        self.quantity = QSpinBox(); self.quantity.setRange(100, 999999); self.quantity.setSingleStep(100)
        self.due_date = QDateEdit(QDate.currentDate().addDays(7)); self.due_date.setCalendarPopup(True); self.due_date.setMinimumDate(QDate.currentDate())
        self.customer_level = QComboBox(); self.customer_level.addItems(["A", "B", "C"])

        layout = QFormLayout()
        layout.addRow("订单ID:", self.order_id); layout.addRow("产品名称:", self.product_name)
        layout.addRow("数量(米):", self.quantity); layout.addRow("交货日期:", self.due_date)
        layout.addRow("客户等级:", self.customer_level)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self); main_layout.addLayout(layout); main_layout.addWidget(btns)

        if order_data:
            self.order_id.setText(order_data.get("id", "")); self.order_id.setReadOnly(True)
            self.product_name.setText(order_data.get("product", ""))
            self.quantity.setValue(order_data.get("quantity", 100))
            due_date_obj = order_data.get("due_date")
            if isinstance(due_date_obj, datetime.date):
                self.due_date.setDate(QDate(due_date_obj.year, due_date_obj.month, due_date_obj.day))
            self.customer_level.setCurrentText(order_data.get("customer_level", "C"))
            
    def get_data(self):
        return {"id": self.order_id.text(), "product": self.product_name.text(), 
                "quantity": self.quantity.value(), "due_date": self.due_date.date().toPyDate(),
                "customer_level": self.customer_level.currentText()}