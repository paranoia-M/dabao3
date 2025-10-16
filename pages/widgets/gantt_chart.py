# pages/widgets/gantt_chart.py
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPen
import random

# --- 常量定义 ---
LINE_HEIGHT = 60
HOUR_WIDTH = 80
HEADER_HEIGHT = 40
LINE_LABEL_WIDTH = 100

class TaskBlockItem(QGraphicsRectItem):
    """自定义的甘特图任务块 (已移除信号)"""
    # --- 1. 移除 pyqtSignal ---
    # rescheduled = pyqtSignal(str, int, int) # <- REMOVED

    # --- 2. 接受 view 作为参数 ---
    def __init__(self, view, order, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view # 存储对父视图的引用
        self.order_data = order
        self.original_pos = QPointF()

        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 1))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        
        self.text = QGraphicsTextItem(f"{order['id']}\n{order['product']}", self)
        self.text.setDefaultTextColor(Qt.white)
        self.text.setPos(5, 5)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            grid_x = round(new_pos.x() / HOUR_WIDTH) * HOUR_WIDTH
            grid_y = round(new_pos.y() / LINE_HEIGHT) * LINE_HEIGHT
            grid_x = max(0, grid_x)
            grid_y = max(0, grid_y)
            scene_rect = self.scene().sceneRect()
            if grid_x + self.rect().width() > scene_rect.right(): grid_x = scene_rect.right() - self.rect().width()
            if grid_y + self.rect().height() > scene_rect.bottom(): grid_y = scene_rect.bottom() - self.rect().height()
            return QPointF(grid_x, grid_y)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.original_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        scene = self.scene()
        all_tasks = [item for item in scene.items() if isinstance(item, TaskBlockItem) and item is not self]
        
        has_conflict = False
        for task in all_tasks:
            if self.collidesWithItem(task): has_conflict = True; break
        
        if has_conflict:
            self.setPos(self.original_pos)
            print(f"冲突！工单 {self.order_data['id']} 无法放置。")
        else:
            # --- 3. 调用父视图的方法来发射信号 ---
            new_line_index = int(self.pos().y() / LINE_HEIGHT)
            new_start_hour = int(self.pos().x() / HOUR_WIDTH)
            # 只有当位置真正改变时才通知
            if self.pos() != self.original_pos:
                self.view.notify_task_rescheduled(self.order_data['id'], new_line_index, new_start_hour)


class ScheduleGanttView(QGraphicsView):
    """自定义的甘特图视图 (现在负责发射所有信号)"""
    task_dropped = pyqtSignal(str, int, int)
    # --- 4. 在这里定义 reschedule 信号 ---
    task_rescheduled = pyqtSignal(str, int, int)

    def __init__(self, production_lines, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.production_lines = production_lines
        self.total_hours = 24

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self._draw_background()

    def _draw_background(self):
        self.scene.clear()
        scene_width = self.total_hours * HOUR_WIDTH
        scene_height = len(self.production_lines) * LINE_HEIGHT
        self.scene.setSceneRect(-LINE_LABEL_WIDTH, -HEADER_HEIGHT, scene_width + LINE_LABEL_WIDTH, scene_height + HEADER_HEIGHT)
        for hour in range(self.total_hours):
            x = hour * HOUR_WIDTH
            self.scene.addLine(x, -HEADER_HEIGHT, x, scene_height, QPen(QColor("#455A64")))
            text = self.scene.addText(f"{hour}:00"); text.setDefaultTextColor(QColor("#B0BEC5")); text.setPos(x + 5, -HEADER_HEIGHT + 5)
        for i, line_name in enumerate(self.production_lines):
            y = i * LINE_HEIGHT
            self.scene.addLine(0, y, scene_width, y, QPen(QColor("#455A64")))
            text = self.scene.addText(line_name); text.setDefaultTextColor(QColor("#B0BEC5")); text.setPos(-LINE_LABEL_WIDTH + 10, y + (LINE_HEIGHT / 2) - 10)
        self.scene.addLine(0, scene_height, scene_width, scene_height, QPen(QColor("#455A64")))

    def add_task(self, order, line_index, start_hour, duration_hours):
        color = QColor(random.choice(["#0097A7", "#D32F2F", "#512DA8", "#0288D1", "#388E3C"]))
        rect = QRectF(0, 0, duration_hours * HOUR_WIDTH - 2, LINE_HEIGHT - 2)
        # --- 5. 创建 TaskBlockItem 时传入 self (view) ---
        task_item = TaskBlockItem(self, order, color, rect)
        x = start_hour * HOUR_WIDTH + 1
        y = line_index * LINE_HEIGHT + 1
        task_item.setPos(x, y)
        self.scene.addItem(task_item)
        return task_item

    # --- 6. 新增一个方法，由 TaskBlockItem 调用 ---
    def notify_task_rescheduled(self, order_id, new_line_index, new_start_hour):
        """由子项调用，然后由自己发射信号"""
        print(f"成功！工单 {order_id} 已重新排程。")
        self.task_rescheduled.emit(order_id, new_line_index, new_start_hour)

    def set_total_hours(self, hours):
        self.total_hours = hours; self._draw_background()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        order_id = event.mimeData().text()
        drop_pos = self.mapToScene(event.pos())
        line_index = int(drop_pos.y() / LINE_HEIGHT)
        start_hour = int(drop_pos.x() / HOUR_WIDTH)
        if 0 <= line_index < len(self.production_lines) and start_hour >= 0:
            self.task_dropped.emit(order_id, line_index, start_hour)
        event.acceptProposedAction()