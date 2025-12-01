import sys
import os
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QFileDialog, QTableView, QSplitter,
                               QScrollArea, QLabel, QSlider, QLineEdit, QMenu, QMessageBox)
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut, QDoubleValidator
from PySide6.QtCore import QAbstractTableModel, Qt, Signal, QObject

from src.logger import setup_logging
from src.data_model import DataModel
from src.image_view import ImageView
from src.config_manager import ConfigManager
from src.settings_dialog import SettingsDialog
from src.version_checker import check_for_updates
import logging

__version__ = "0.1.1"

class MainController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ThotIndex - Indexeur de tableaux v{__version__}")
        self.resize(1200, 800)
        
        self.logger = logging.getLogger(__name__)
        self.data_model = DataModel()
        self.config = ConfigManager()
        
        self.calibration_widgets = {} # col_index -> QLineEdit
        self.calibration_labels = {} # col_index -> QLabel
        
        self.setup_ui()
        self.setup_menu()
        self.setup_shortcuts()
        self.setup_global_shortcuts()
        self.apply_modern_theme()
        
        # Check for updates asynchronously
        self.check_version_async()

    def apply_modern_theme(self):
        """Apply theme using colors from config."""
        config = self.config
        bg = config.config.get("colors", {}).get("background", "#2b2b2b")
        btn_primary = config.config.get("colors", {}).get("button_primary", "#007acc")
        btn_hover = config.config.get("colors", {}).get("button_hover", "#0098ff")
        btn_pressed = config.config.get("colors", {}).get("button_pressed", "#005c99")
        btn_checked = config.config.get("colors", {}).get("button_checked", "#005c99")
        
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {bg};
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }}
            
            QPushButton {{
                background-color: {btn_primary};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
            QPushButton:checked {{
                background-color: {btn_checked};
                border: 1px solid #00aaff;
            }}
            
            QTableView {{
                background-color: #1e1e1e;
                gridline-color: #333333;
                selection-background-color: {btn_primary};
                selection-color: white;
                border: 1px solid #333333;
            }}
            QHeaderView::section {{
                background-color: #333333;
                color: white;
                padding: 4px;
                border: 1px solid {bg};
            }}
            
            QSlider::groove:horizontal {{
                border: 1px solid #333333;
                height: 8px;
                background: #1e1e1e;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {btn_primary};
                border: 1px solid {btn_primary};
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {btn_hover};
            }}
            
            QLineEdit {{
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px;
                color: white;
            }}
            QLineEdit:focus {{
                border: 1px solid {btn_primary};
            }}
            
            QSplitter::handle {{
                background-color: #333333;
            }}
            
            QScrollArea {{
                border: none;
                background-color: {bg};
            }}
            
            QLabel {{
                color: #e0e0e0;
            }}
        """)

    def setup_calibration_ui(self):
        # Clear existing
        for i in reversed(range(self.calibration_layout.count())): 
            self.calibration_layout.itemAt(i).widget().setParent(None)
        self.calibration_widgets.clear()
        
        if self.data_model.df is None:
            return
            
        headers = self.data_model.df.columns
        for i, header in enumerate(headers):
            # Container
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(2, 2, 2, 2)
            
            lbl = QLabel(header[:10]) # Truncate
            lbl.setToolTip(header)
            
            # Text Field for Percentage
            txt = QLineEdit()
            txt.setValidator(QDoubleValidator(0.0, 100.0, 2))
            txt.setFixedWidth(60)
            
            # Set initial value
            initial_val = self.data_model.column_centers.get(i, 0.5) * 100
            txt.setText(f"{initial_val:.1f}")
            
            # Connect signal (editingFinished to avoid too many updates while typing)
            txt.editingFinished.connect(lambda col=i: self.on_calibration_changed(col))
            
            vbox.addWidget(lbl)
            vbox.addWidget(txt)
            
            self.calibration_layout.addWidget(container)
            self.calibration_widgets[i] = txt

    def on_calibration_changed(self, col):
        widget = self.calibration_widgets.get(col)
        if not widget:
            return
            
        try:
            val = float(widget.text())
            ratio = val / 100.0
            ratio = max(0.0, min(1.0, ratio)) # Clamp
            
            # Update DataModel (this triggers redistribution)
            self.data_model.update_column_center(col, ratio)
            
            # Update ALL widgets to reflect new values (redistribution)
            for i, w in self.calibration_widgets.items():
                new_center = self.data_model.column_centers.get(i, 0.5)
                w.setText(f"{new_center * 100:.1f}")
                
        except ValueError:
            pass # Ignore invalid input
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Splitter for Image and Table
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Image View
        self.image_view = ImageView()
        self.image_view.setMinimumHeight(int(self.height() / 3))
        splitter.addWidget(self.image_view)
        
        # Calibration Area (Scrollable)
        self.calibration_area = QScrollArea()
        self.calibration_area.setFixedHeight(80)
        self.calibration_area.setWidgetResizable(True)
        self.calibration_content = QWidget()
        self.calibration_layout = QHBoxLayout(self.calibration_content)
        self.calibration_area.setWidget(self.calibration_content)
        splitter.addWidget(self.calibration_area)
        
        # Table View
        self.table_view = QTableView()
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.table_view)
        
        layout.addWidget(splitter)
        
        # Connect signals
        self.image_view.bboxSelected.connect(self.on_bbox_selected)
        self.image_view.bboxModified.connect(self.on_bbox_modified)
        self.image_view.bboxCreated.connect(self.on_bbox_created)

    def setup_shortcuts(self):
        self.undo_shortcut = QShortcut(QKeySequence.Undo, self)
        self.undo_shortcut.activated.connect(self.undo)
    
    def setup_menu(self):
        """Setup menu bar with settings."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Fichier")
        
        load_image_action = file_menu.addAction("Charger une &Image...")
        load_image_action.triggered.connect(self.load_image)
        
        file_menu.addSeparator()
        
        save_tsv_action = file_menu.addAction("&Sauver le TSV")
        save_tsv_action.setShortcut("Ctrl+S")
        save_tsv_action.triggered.connect(self.save_tsv)
        
        file_menu.addSeparator()
        
        add_box_action = file_menu.addAction("&Nouvelle boite")
        add_box_action.setShortcut("N")
        add_box_action.triggered.connect(lambda: self.btn_create.setChecked(not self.btn_create.isChecked()))
        
        # Settings menu
        settings_menu = menubar.addMenu("&Paramètres")
        
        config_action = settings_menu.addAction("&Configuration...")
        config_action.triggered.connect(self.show_settings_dialog)
    
    def setup_global_shortcuts(self):
        """Setup global keyboard shortcuts for navigation and zoom."""
        config = self.config
        
        # Zoom shortcuts
        zoom_in_shortcut = QShortcut(QKeySequence(config.get_shortcut('zoom_in')), self)
        zoom_in_shortcut.activated.connect(self.image_view.zoom_in)
        
        zoom_out_shortcut = QShortcut(QKeySequence(config.get_shortcut('zoom_out')), self)
        zoom_out_shortcut.activated.connect(self.image_view.zoom_out)
        
        zoom_reset_shortcut = QShortcut(QKeySequence(config.get_shortcut('zoom_reset')), self)
        zoom_reset_shortcut.activated.connect(self.image_view.zoom_reset)
        
        # Pan shortcuts
        pan_step = config.get_ui_param('pan_step')
        
        pan_up_shortcut = QShortcut(QKeySequence(config.get_shortcut('pan_up')), self)
        pan_up_shortcut.activated.connect(lambda: self.image_view.pan(0, -pan_step))
        
        pan_down_shortcut = QShortcut(QKeySequence(config.get_shortcut('pan_down')), self)
        pan_down_shortcut.activated.connect(lambda: self.image_view.pan(0, pan_step))
        
        pan_left_shortcut = QShortcut(QKeySequence(config.get_shortcut('pan_left')), self)
        pan_left_shortcut.activated.connect(lambda: self.image_view.pan(-pan_step, 0))
        
        pan_right_shortcut = QShortcut(QKeySequence(config.get_shortcut('pan_right')), self)
        pan_right_shortcut.activated.connect(lambda: self.image_view.pan(pan_step, 0))
        
        # BBox creation shortcut
        create_bbox_shortcut = QShortcut(QKeySequence(config.get_shortcut('create_bbox')), self)
        create_bbox_shortcut.activated.connect(self.image_view.toggle_creation_mode)
        create_bbox_shortcut.activated.connect(lambda: self.btn_create.setChecked(self.image_view.creation_mode))

        # Toggle Calibration shortcut
        toggle_calibration_shortcut = QShortcut(QKeySequence(config.get_shortcut('toggle_calibration')), self)
        toggle_calibration_shortcut.activated.connect(self.toggle_calibration)

    def toggle_calibration(self):
        """Toggle visibility of the calibration area."""
        is_visible = self.calibration_area.isVisible()
        self.calibration_area.setVisible(not is_visible)
        # Also hide the splitter handle if possible, or just the widget is enough.
        # When a widget in a splitter is hidden, the splitter usually handles it.
    
    def check_version_async(self):
        """Check for updates asynchronously to avoid blocking startup."""
        def version_check_thread():
            is_newer, latest_version = check_for_updates(__version__)
            # Safely invoke the UI update from the main thread
            if is_newer and latest_version:
                # Use Qt's signal mechanism or direct call depending on thread safety
                # For simplicity, we'll use QMetaObject.invokeMethod or similar
                # But since we can't easily cross thread boundaries, we'll use a simple approach
                self.on_version_check_complete(is_newer, latest_version)
        
        # Start the check in a background thread
        thread = threading.Thread(target=version_check_thread, daemon=True)
        thread.start()
    
    def on_version_check_complete(self, is_newer, latest_version):
        """Handle the result of the version check."""
        if is_newer:
            QMessageBox.information(
                self,
                "Mise à jour disponible / Update Available",
                f"Une nouvelle version est disponible : {latest_version}\n"
                f"Version actuelle : {__version__}\n\n"
                f"A new version is available: {latest_version}\n"
                f"Current version: {__version__}\n\n"
                f"Visitez / Visit: https://github.com/Sidam31/ThotIndex/releases"
            )
    
    def show_settings_dialog(self):
        """Show settings dialog and reload shortcuts/theme if settings changed."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()
    
    def on_settings_changed(self):
        """Reload configuration and update UI."""
        self.logger.info("Settings changed, reloading configuration")
        # Reload config
        self.config = ConfigManager()
        # Reapply theme
        self.apply_modern_theme()
        # Recreate shortcuts (simple approach: restart required for shortcuts)
        # For full dynamic reload, we'd need to store and recreate all QShortcut objects
        QMessageBox = __import__('PySide6.QtWidgets', fromlist=['QMessageBox']).QMessageBox
        QMessageBox.information(
            self,
            "Paramètres modifiés",
            "Certains paramètres nécessitent un redémarrage de l'application pour prendre effet."
        )

    def undo(self):
        if self.data_model.undo():
            self.logger.info("Undo performed")
            if hasattr(self, 'model'):
                self.model.layoutChanged.emit()
            self.draw_bboxes()
            self.image_view.scene.update()

    def toggle_creation_mode(self, checked):
        self.image_view.creation_mode = checked
        if checked:
            self.image_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.image_view.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.image_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.image_view.setCursor(Qt.CursorShape.ArrowCursor)

    def load_files(self):
        # For now, ask for Image, then TSV
        img_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.tif)")
        if not img_path:
            return
            
        tsv_path, _ = QFileDialog.getOpenFileName(self, "Open TSV", os.path.dirname(img_path), "TSV Files (*.tsv *.csv *.txt)")
        if not tsv_path:
            return
            
        self.logger.info(f"Loading {img_path} and {tsv_path}")
        
        # Load Image
        pixmap = QPixmap(img_path)
        self.image_view.set_image(pixmap)
        
        # Store image filepath in data_model
        self.data_model.image_filepath = img_path
        
        # Load Data
        try:
            self.data_model.load_data(tsv_path)
            self.populate_table()
            self.setup_calibration_ui()
            self.draw_bboxes()
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
    
    def load_image(self):
        """Load an image file separately."""
        img_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.tif)")
        if not img_path:
            return
        
        self.logger.info(f"Loading image: {img_path}")
        
        # Load Image
        pixmap = QPixmap(img_path)
        self.image_view.set_image(pixmap)
        
        # Store image filepath in data_model
        self.data_model.image_filepath = img_path
        
        # Save config if TSV is already loaded
        if self.data_model.filepath:
            self.data_model.save_config()
        
        # Redraw bboxes if data is loaded
        if self.data_model.df is not None:
            self.draw_bboxes()
        tsv_path = os.path.splitext(img_path)[0] + ".tsv"
        if not os.path.exists(tsv_path):
            tsv_path = None
        self.load_tsv(tsv_path)
    
    def load_tsv(self, tsv_path=None):
        """Load a TSV file separately."""
        if tsv_path is None:
            tsv_path, _ = QFileDialog.getOpenFileName(self, "Open TSV", "", "TSV Files (*.tsv *.csv *.txt)")
        if not tsv_path:
            return
        
        self.logger.info(f"Loading TSV: {tsv_path}")
        
        # Load Data
        try:
            self.data_model.load_data(tsv_path)
            self.populate_table()
            self.setup_calibration_ui()
            
            # Draw bboxes if image is loaded
            if not self.image_view.pixmap_item.pixmap().isNull():
                self.draw_bboxes()
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")

    def setup_calibration_ui(self):
        # Clear existing
        for i in reversed(range(self.calibration_layout.count())): 
            self.calibration_layout.itemAt(i).widget().setParent(None)
        self.calibration_widgets.clear()
        self.calibration_labels = {} # col_index -> QLabel
        
        if self.data_model.df is None:
            return
            
        headers = self.data_model.df.columns
        
        # Add Spacer before first slider
        spacer = QWidget()
        spacer.setFixedWidth(100) # Minimum width as requested
        self.calibration_layout.addWidget(spacer)
        
        # Skip the first column (index 0)
        for i, header in enumerate(headers):
            if i == 0:
                continue
                
            # Container
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(2, 2, 2, 2)
            
            lbl = QLabel(header[:10]) # Truncate
            lbl.setToolTip(header)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50) # Default 0.5
            slider.valueChanged.connect(lambda val, col=i: self.on_calibration_changed(col, val))
            
            vbox.addWidget(lbl)
            vbox.addWidget(slider)
            
            self.calibration_layout.addWidget(container)
            self.calibration_widgets[i] = slider
            self.calibration_labels[i] = lbl

    def on_calibration_changed(self, col, val):
        ratio = val / 100.0
        self.data_model.update_column_center(col, ratio)
        
        # Update ALL widgets to reflect new values (redistribution)
        for i, w in self.calibration_widgets.items():
            new_center = self.data_model.column_centers.get(i, 0.5)
            w.blockSignals(True) # Prevent recursion
            w.setValue(int(new_center * 100))
            w.blockSignals(False)
        
        # Update view if this column is selected
        selection = self.table_view.selectionModel().currentIndex()
        if selection.isValid() and selection.column() == col:
            row = selection.row()
            bbox = self.data_model.get_bbox(row)
            if bbox:
                self.image_view.focus_on_cell(bbox, ratio)

    def populate_table(self):
        if self.data_model.df is not None:
            from src.pandas_model import PandasModel
            self.model = PandasModel(self.data_model) # Pass data_model
            self.table_view.setModel(self.model)
            # Connect selection model
            self.table_view.selectionModel().currentChanged.connect(self.on_table_selection_changed)

    def draw_bboxes(self):
        count = self.data_model.row_count()
        for i in range(count):
            bbox = self.data_model.get_bbox(i)
            if bbox:
                self.image_view.add_bbox(i, bbox)

    def save_tsv(self):
        try:
            self.data_model.save_data()
            self.logger.info("Data saved.")
        except Exception as e:
            self.logger.error(f"Error saving: {e}")

    def on_bbox_selected(self, row_index):
        self.table_view.selectRow(row_index)
        self.logger.debug(f"Selected row {row_index}")

    def on_table_selection_changed(self, current, previous):
        if not current.isValid():
            return
            
        row = current.row()
        col = current.column()
        
        # Update Label Styles
        # Reset previous
        if previous.isValid():
            prev_col = previous.column()
            if prev_col in self.calibration_labels:
                font = self.calibration_labels[prev_col].font()
                font.setBold(False)
                self.calibration_labels[prev_col].setFont(font)
        
        # Set current
        if col in self.calibration_labels:
            font = self.calibration_labels[col].font()
            font.setBold(True)
            self.calibration_labels[col].setFont(font)
        
        bbox = self.data_model.get_bbox(row)
        if bbox:
            center_ratio = self.data_model.column_centers.get(col, 0.5)
            self.image_view.focus_on_cell(bbox, center_ratio)

    def on_bbox_modified(self, row_index, bbox):
        self.data_model.update_bbox(row_index, bbox)
        if hasattr(self, 'model'):
            self.model.layoutChanged.emit()

    def on_bbox_created(self, bbox):
        new_index = self.data_model.add_row(bbox)
        if hasattr(self, 'model'):
            self.model.layoutChanged.emit()
        self.image_view.add_bbox(new_index, bbox)
        # Optional: Select the new row
        self.table_view.selectRow(new_index)

    def show_context_menu(self, position):
        """
        Shows a context menu on the table view with option to revert cell to original.
        """
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return
        
        menu = QMenu()
        revert_action = menu.addAction("Revert to Original")
        
        action = menu.exec_(self.table_view.viewport().mapToGlobal(position))
        
        if action == revert_action:
            row = index.row()
            col = index.column()
            if self.data_model.revert_cell(row, col):
                if hasattr(self, 'model'):
                    self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole])
                self.logger.info(f"Reverted cell ({row}, {col}) to original value")

if __name__ == "__main__":
    setup_logging()
    app = QApplication(sys.argv)
    window = MainController()
    window.show()
    sys.exit(app.exec())
