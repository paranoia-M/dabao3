# pages/widgets/fishbone_diagram.py
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class FishboneNode(pg.GraphicsObject):
    def __init__(self, data, is_major=False):
        super().__init__()
        self.data = data
        
        # --- 核心修正点 1: 在创建时就设置颜色 ---
        self.suspicion_colors = {
            'high': '#D32F2F', 'medium': '#F57C00', 
            'low': '#FBC02D', 'none': '#212121'
        }
        initial_color = self.suspicion_colors[self.data['suspicion']]

        self.text_item = pg.TextItem(self.data['label'], color=initial_color)
        
        if is_major:
            font = QFont(); font.setBold(True); font.setPointSize(12)
            self.text_item.setFont(font)
        
        self.setAcceptHoverEvents(True)

    # --- 核心修正点 2: 使用setColor来更新颜色 ---
    def update_color(self):
        color = self.suspicion_colors[self.data['suspicion']]
        self.text_item.setColor(color)

    def hoverEnterEvent(self, event):
        self.text_item.setColor(QColor(0, 150, 255)) # Highlight with blue
        self.setCursor(Qt.PointingHandCursor)
    
    def hoverLeaveEvent(self, event):
        self.update_color() # Restore original color
        self.setCursor(Qt.ArrowCursor)
    
    def boundingRect(self): return self.text_item.boundingRect()
    def paint(self, p, *args): pass

    def setPos(self, *args):
        super().setPos(*args)
        self.text_item.setPos(*args)


class FishboneDiagram(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()
        self.setBackground(None); self.ci.layout.setSpacing(0)
        self.plot = self.addPlot(row=0, col=0)
        self.plot.hideAxis('left'); self.plot.hideAxis('bottom')
        self.plot.setAspectLocked()

    def draw(self, problem, causes, node_click_handler):
        self.plot.clear()
        
        line_pen = pg.mkPen('#616161', width=2)
        text_color = '#212121'
        
        head_text = pg.TextItem(problem, color=text_color, anchor=(0, 0.5))
        font = QFont(); font.setBold(True); font.setPointSize(16)
        head_text.setFont(font); head_text.setPos(100, 0)
        self.plot.addItem(head_text); self.plot.plot([0, 95], [0, 0], pen=line_pen)

        major_bones = {'人': {'angle': 45, 'length': 40, 'text_anchor': (0, 1)}, '机': {'angle': -45, 'length': 40, 'text_anchor': (0, 0)},
                       '料': {'angle': 135, 'length': 40, 'text_anchor': (1, 1)}, '法': {'angle': -135, 'length': 40, 'text_anchor': (1, 0)}}
        
        for category, config in major_bones.items():
            if category not in causes or not causes[category]: continue
            
            angle_rad = np.deg2rad(config['angle'])
            start_point = (np.cos(angle_rad) * 10, 0)
            end_point = (np.cos(angle_rad) * config['length'], np.sin(angle_rad) * config['length'])
            
            self.plot.plot([start_point[0], end_point[0]], [0, end_point[1]], pen=line_pen)
            
            cat_node_data = {'label': category, 'suspicion': 'none', 'details': f"分析与'{category}'相关的因素。"}
            cat_node = FishboneNode(cat_node_data, is_major=True)
            cat_node.mousePressEvent = lambda event, data=cat_node_data: node_click_handler(data)
            self.plot.addItem(cat_node.text_item) # --- 核心修正点 3: 添加内部的 TextItem ---
            cat_node.setPos(end_point[0], end_point[1])

            num_items = len(causes[category])
            for i, item_data in enumerate(causes[category]):
                pos_on_bone = (i + 1) / (num_items + 1.0)
                sub_start_x, sub_start_y = pos_on_bone * end_point[0], pos_on_bone * end_point[1]
                sub_angle_rad = angle_rad + np.deg2rad(90 * np.sign(end_point[1]))
                sub_length = 15
                sub_end_x, sub_end_y = sub_start_x + np.cos(sub_angle_rad) * sub_length, sub_start_y + np.sin(sub_angle_rad) * sub_length
                
                self.plot.plot([sub_start_x, sub_end_x], [sub_start_y, sub_end_y], pen=line_pen)
                
                item_node = FishboneNode(item_data)
                item_node.mousePressEvent = lambda event, data=item_data: node_click_handler(data)
                self.plot.addItem(item_node.text_item) # --- 核心修正点 3: 添加内部的 TextItem ---
                if sub_end_x > sub_start_x: item_node.text_item.setAnchor((0, 0.5))
                else: item_node.text_item.setAnchor((1, 0.5))
                item_node.setPos(sub_end_x, sub_end_y)
        self.plot.autoRange()