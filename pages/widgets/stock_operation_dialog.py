# pages/widgets/stock_operation_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox, 
                             QDialogButtonBox, QLabel, QMessageBox)

class StockOperationDialog(QDialog):
    def __init__(self, parent=None, material_name="", current_stock=0, mode='in'):
        super().__init__(parent)
        self.current_stock = current_stock
        self.mode = mode

        # UI 组件
        info_label = QLabel(f"<b>物料:</b> {material_name}<br><b>当前库存:</b> {current_stock}")
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999999)
        
        form_layout = QFormLayout()
        
        if self.mode == 'in':
            self.setWindowTitle("物料入库")
            form_layout.addRow("入库数量:", self.quantity_input)
        else: # 'out'
            self.setWindowTitle("物料出库")
            form_layout.addRow("出库数量:", self.quantity_input)
            # 特色逻辑：出库时，最大值不能超过当前库存
            self.quantity_input.setRange(1, self.current_stock)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(info_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        
    def validate_and_accept(self):
        """在接受前进行校验"""
        quantity = self.quantity_input.value()
        if self.mode == 'out' and quantity > self.current_stock:
            QMessageBox.warning(self, "库存不足", "出库数量不能大于当前库存！")
            return
        self.accept()

    def get_quantity(self):
        return self.quantity_input.value()