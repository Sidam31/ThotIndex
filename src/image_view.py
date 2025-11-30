from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QCursor
from src.config_manager import ConfigManager

class BBoxItem(QGraphicsRectItem):
    def __init__(self, rect, row_index, view):
        super().__init__(rect)
        self.row_index = row_index
        self.view = view
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Colors from config
        config = ConfigManager()
        border_color = config.get_color('bbox_border')
        fill_color = config.get_color('bbox_fill')
        
        pen = QPen(border_color, 2)
        self.setPen(pen)
        self.setBrush(QBrush(fill_color))
        self.setAcceptHoverEvents(True)
        
        self.resizing = False
        self.resize_start_pos = None
        self.resize_start_rect = None

    def hoverMoveEvent(self, event):
        # Check if near bottom-right corner (in local coords)
        rect = self.rect()
        pos = event.pos()
        
        # Adaptive margin based on zoom level
        view_scale = self.view.transform().m11()
        config = ConfigManager()
        base_margin = config.get_ui_param('bbox_resize_margin')
        margin = base_margin / view_scale if view_scale > 0 else base_margin
        
        if (rect.right() - margin < pos.x() < rect.right() + margin) and \
           (rect.bottom() - margin < pos.y() < rect.bottom() + margin):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self.cursor().shape() == Qt.CursorShape.SizeFDiagCursor:
            self.resizing = True
            self.resize_start_pos = event.pos()
            self.resize_start_rect = self.rect()
            event.accept()
        else:
            super().mousePressEvent(event)
            self.view.bboxSelected.emit(self.row_index)

    def mouseMoveEvent(self, event):
        if self.resizing:
            diff = event.pos() - self.resize_start_pos
            new_rect = self.resize_start_rect.adjusted(0, 0, diff.x(), diff.y())
            self.setRect(new_rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            self.view.notify_bbox_changed(self)
        else:
            super().mouseReleaseEvent(event)
            # If moved, notify
            # We can check if pos changed, or just always notify on release
            self.view.notify_bbox_changed(self)

class ImageView(QGraphicsView):
    bboxSelected = Signal(int) # Emits row_index
    bboxModified = Signal(int, list) # Emits row_index, [ymin, xmin, ymax, xmax] (0-1000)
    bboxCreated = Signal(list) # Emits [ymin, xmin, ymax, xmax]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        
        self.pixmap_item = None
        self.image_width = 0
        self.image_height = 0
        
        self.current_bboxes = {} # row_index -> BBoxItem
        
        # Creation Mode
        self.creation_mode = False
        self.temp_rect_item = None
        self.start_creation_pos = None

    def set_image(self, pixmap):
        self.scene.clear()
        self.current_bboxes.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        self.setSceneRect(0, 0, self.image_width, self.image_height)

    def add_bbox(self, row_index, bbox_norm):
        if self.image_width == 0 or self.image_height == 0:
            return

        ymin, xmin, ymax, xmax = bbox_norm
        
        x = (xmin / 1000.0) * self.image_width
        y = (ymin / 1000.0) * self.image_height
        w = ((xmax - xmin) / 1000.0) * self.image_width
        h = ((ymax - ymin) / 1000.0) * self.image_height
        
        rect = QRectF(x, y, w, h)
        item = BBoxItem(rect, row_index, self)
        self.scene.addItem(item)
        self.current_bboxes[row_index] = item

    def notify_bbox_changed(self, item):
        # Get absolute rect in scene
        # item.rect() is local. item.pos() is offset.
        # scene_rect = item.mapRectToScene(item.rect()) 
        # Actually BBoxItem is a RectItem, so its rect() is the geometry. 
        # If moved, pos() changes. If resized, rect() changes.
        # We need the combination.
        
        scene_rect = item.mapRectToScene(item.rect())
        
        ymin = int((scene_rect.top() / self.image_height) * 1000)
        xmin = int((scene_rect.left() / self.image_width) * 1000)
        ymax = int((scene_rect.bottom() / self.image_height) * 1000)
        xmax = int((scene_rect.right() / self.image_width) * 1000)
        
        # Clamp
        ymin = max(0, min(1000, ymin))
        xmin = max(0, min(1000, xmin))
        ymax = max(0, min(1000, ymax))
        xmax = max(0, min(1000, xmax))
        
        self.bboxModified.emit(item.row_index, [ymin, xmin, ymax, xmax])

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
             # Standard zoom
             pass
        
        zoom_in = event.angleDelta().y() > 0
        factor = 1.1 if zoom_in else 0.9
        self.scale(factor, factor)

    def zoom_in(self):
        """Zoom in on the image."""
        config = ConfigManager()
        factor = config.get_ui_param('zoom_factor')
        self.scale(factor, factor)
    
    def zoom_out(self):
        """Zoom out on the image."""
        config = ConfigManager()
        factor = config.get_ui_param('zoom_factor')
        self.scale(1.0 / factor, 1.0 / factor)
    
    def zoom_reset(self):
        """Reset zoom to fit the entire image."""
        self.resetTransform()
        if self.pixmap_item:
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def pan(self, dx, dy):
        """Pan the view by dx, dy pixels."""
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        h_bar.setValue(h_bar.value() + dx)
        v_bar.setValue(v_bar.value() + dy)
    
    def toggle_creation_mode(self):
        """Toggle bbox creation mode."""
        self.creation_mode = not self.creation_mode
        if self.creation_mode:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def keyPressEvent(self, event):
        # Creation mode toggle is now handled by shortcut in main.py
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.creation_mode:
            pos = self.mapToScene(event.position().toPoint())
            self.start_creation_pos = pos
            self.temp_rect_item = QGraphicsRectItem(QRectF(pos, pos))
            self.temp_rect_item.setPen(QPen(Qt.blue, 2, Qt.PenStyle.DashLine))
            self.scene.addItem(self.temp_rect_item)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.creation_mode and self.temp_rect_item:
            pos = self.mapToScene(event.position().toPoint())
            rect = QRectF(self.start_creation_pos, pos).normalized()
            self.temp_rect_item.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.creation_mode and self.temp_rect_item:
            rect = self.temp_rect_item.rect()
            self.scene.removeItem(self.temp_rect_item)
            self.temp_rect_item = None
            
            # Convert to 0-1000
            ymin = int((rect.top() / self.image_height) * 1000)
            xmin = int((rect.left() / self.image_width) * 1000)
            ymax = int((rect.bottom() / self.image_height) * 1000)
            xmax = int((rect.right() / self.image_width) * 1000)
            
            self.bboxCreated.emit([ymin, xmin, ymax, xmax])
            
            # Exit creation mode? Or stay? Let's stay for multiple adds.
            # self.creation_mode = False
            # self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            # self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def focus_on_cell(self, bbox_norm, center_ratio=0.5):
        """
        Zooms to the row and centers horizontally based on center_ratio (0.0 to 1.0).
        bbox_norm: [ymin, xmin, ymax, xmax] (0-1000)
        """
        if self.image_width == 0 or self.image_height == 0:
            return

        ymin, xmin, ymax, xmax = bbox_norm
        
        # Convert Y to pixels
        y = (ymin / 1000.0) * self.image_height
        h = ((ymax - ymin) / 1000.0) * self.image_height
        
        # Calculate X based on center_ratio
        # row_x = (xmin / 1000.0) * self.image_width
        # row_w = ((xmax - xmin) / 1000.0) * self.image_width
        # Actually, we want to center the view on (center_ratio * image_width)
        # But constrained by the row's vertical position.
        
        center_x = center_ratio * self.image_width
        
        # Define a view width. Let's say 20% of image width by default, 
        # or we can try to infer cell width if we had it. 
        # Without cell width, we just center the view.
        view_w = self.image_width / 5 
        
        view_x = center_x - (view_w / 2)
        
        # Define the target rectangle to view
        target_rect = QRectF(view_x, y, view_w, h)
            
        self.fitInView(target_rect, Qt.AspectRatioMode.KeepAspectRatio)
