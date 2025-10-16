# pages/widgets/material_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QComboBox, QDialogButtonBox)

class MaterialDialog(QDialog):
    def __init__(self, parent=None, material_data=None):
        super().__init__(parent)
        
        # UI 组件
        self.material_id_input = QLineEdit()
        self.material_name_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["原料", "辅料", "半成品", "包装材料"])
        self.unit_input = QLineEdit()
        self.safety_stock_input = QSpinBox()
        self.safety_stock_input.setRange(0, 999999)

        form_layout = QFormLayout()
        form_layout.addRow("物料编码:", self.material_id_input)
        form_layout.addRow("物料名称:", self.material_name_input)
        form_layout.addRow("物料类别:", self.category_input)
        form_layout.addRow("单位:", self.unit_input)
        form_layout.addRow("安全库存:", self.safety_stock_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        if material_data:
            self.setWindowTitle("编辑物料")
            self.material_id_input.setText(material_data.get("id", ""))
            self.material_id_input.setReadOnly(True)
            self.material_name_input.setText(material_data.get("name", ""))
            self.category_input.setCurrentText(material_data.get("category", "原料"))
            self.unit_input.setText(material_data.get("unit", ""))
            self.safety_stock_input.setValue(material_data.get("safety_stock", 0))
        else:
            self.setWindowTitle("添加新物料")

    def get_data(self):
        return {
            "id": self.material_id_input.text(),
            "name": self.material_name_input.text(),
            "category": self.category_input.currentText(),
            "unit": self.unit_input.text(),
            "safety_stock": self.safety_stock_input.value(),
        }