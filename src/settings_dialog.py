from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QWidget, QPushButton, QLabel, QLineEdit, QSlider,
                               QColorDialog, QFormLayout, QScrollArea, QMessageBox,
                               QKeySequenceEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence
from src.config_manager import ConfigManager
import logging

class SettingsDialog(QDialog):
    """Dialog for editing application settings."""
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.resize(600, 500)
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager()
        
        # Store temporary changes
        self.temp_shortcuts = {}
        self.temp_colors = {}
        self.temp_ui_params = {}
        
        # Apply dark mode theme
        self.apply_dark_theme()
        
        self.setup_ui()
        self.load_current_settings()
    
    def apply_dark_theme(self):
        """Apply dark mode theme to the dialog."""
        bg = self.config.config.get("colors", {}).get("background", "#2b2b2b")
        btn_primary = self.config.config.get("colors", {}).get("button_primary", "#007acc")
        btn_hover = self.config.config.get("colors", {}).get("button_hover", "#0098ff")
        btn_pressed = self.config.config.get("colors", {}).get("button_pressed", "#005c99")
        
        self.setStyleSheet(f"""
            QDialog, QWidget {{
                background-color: {bg};
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }}
            
            QTabWidget::pane {{
                border: 1px solid #333333;
                background-color: {bg};
            }}
            
            QTabBar::tab {{
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #333333;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {bg};
                color: #ffffff;
                border-bottom: 2px solid {btn_primary};
            }}
            
            QTabBar::tab:hover {{
                background-color: #333333;
            }}
            
            QPushButton {{
                background-color: {btn_primary};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
            
            QLabel {{
                color: #e0e0e0;
            }}
            
            QLineEdit, QKeySequenceEdit {{
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }}
            QLineEdit:focus, QKeySequenceEdit:focus {{
                border: 1px solid {btn_primary};
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
            
            QScrollArea {{
                border: none;
                background-color: {bg};
            }}
            
            QScrollBar:vertical {{
                background-color: #1e1e1e;
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: #555555;
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #666666;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QMessageBox {{
                background-color: {bg};
                color: #ffffff;
            }}
            QMessageBox QLabel {{
                color: #ffffff;
            }}
        """)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.shortcuts_tab = self.create_shortcuts_tab()
        self.colors_tab = self.create_colors_tab()
        self.ui_tab = self.create_ui_tab()
        
        self.tabs.addTab(self.shortcuts_tab, "Raccourcis clavier")
        self.tabs.addTab(self.colors_tab, "Couleurs")
        self.tabs.addTab(self.ui_tab, "Interface")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Rétablir valeurs par défaut")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_changes)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def create_shortcuts_tab(self):
        """Create the shortcuts configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.shortcut_widgets = {}
        
        shortcuts_info = {
            "zoom_in": "Zoom avant",
            "zoom_out": "Zoom arrière",
            "zoom_reset": "Réinitialiser zoom",
            "pan_up": "Déplacer vers le haut",
            "pan_down": "Déplacer vers le bas",
            "pan_left": "Déplacer vers la gauche",
            "pan_right": "Déplacer vers la droite",
            "create_bbox": "Créer BBox",
            "undo": "Annuler",
            "toggle_calibration": "Afficher/Masquer calibration"
        }
        
        for action, label in shortcuts_info.items():
            key_edit = QKeySequenceEdit()
            key_edit.setMaximumSequenceLength(1)
            self.shortcut_widgets[action] = key_edit
            layout.addRow(label + ":", key_edit)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        
        return container
    
    def create_colors_tab(self):
        """Create the colors configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.color_widgets = {}
        
        colors_info = {
            "bbox_border": "Contour BBox",
            "bbox_fill": "Remplissage BBox",
            "modified_cell_bg": "Fond cellule modifiée",
            "button_primary": "Bouton principal",
            "button_hover": "Bouton survolé",
            "button_pressed": "Bouton pressé"
        }
        
        for color_name, label in colors_info.items():
            color_btn = QPushButton("Choisir couleur")
            color_btn.clicked.connect(lambda checked, cn=color_name: self.choose_color(cn))
            
            # Preview label
            preview = QLabel()
            preview.setFixedSize(50, 30)
            preview.setAutoFillBackground(True)
            
            h_layout = QHBoxLayout()
            h_layout.addWidget(preview)
            h_layout.addWidget(color_btn)
            h_layout.addStretch()
            
            self.color_widgets[color_name] = preview
            layout.addRow(label + ":", h_layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        
        return container
    
    def create_ui_tab(self):
        """Create the UI parameters tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.ui_widgets = {}
        
        # Pan step
        pan_slider = QSlider(Qt.Orientation.Horizontal)
        pan_slider.setRange(10, 200)
        pan_slider.setValue(50)
        pan_label = QLabel("50 px")
        pan_slider.valueChanged.connect(lambda v: pan_label.setText(f"{v} px"))
        
        pan_layout = QHBoxLayout()
        pan_layout.addWidget(pan_slider)
        pan_layout.addWidget(pan_label)
        
        self.ui_widgets["pan_step"] = pan_slider
        layout.addRow("Vitesse de déplacement:", pan_layout)
        
        # Zoom factor
        zoom_slider = QSlider(Qt.Orientation.Horizontal)
        zoom_slider.setRange(105, 150)
        zoom_slider.setValue(120)
        zoom_label = QLabel("1.20x")
        zoom_slider.valueChanged.connect(lambda v: zoom_label.setText(f"{v/100:.2f}x"))
        
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(zoom_slider)
        zoom_layout.addWidget(zoom_label)
        
        self.ui_widgets["zoom_factor"] = zoom_slider
        layout.addRow("Facteur de zoom:", zoom_layout)
        
        # BBox resize margin
        margin_slider = QSlider(Qt.Orientation.Horizontal)
        margin_slider.setRange(5, 30)
        margin_slider.setValue(10)
        margin_label = QLabel("10 px")
        margin_slider.valueChanged.connect(lambda v: margin_label.setText(f"{v} px"))
        
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(margin_slider)
        margin_layout.addWidget(margin_label)
        
        self.ui_widgets["bbox_resize_margin"] = margin_slider
        layout.addRow("Marge de redimensionnement BBox:", margin_layout)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(widget)
        container_layout.addStretch()
        
        return container
    
    def load_current_settings(self):
        """Load current settings from config."""
        # Load shortcuts
        for action, widget in self.shortcut_widgets.items():
            shortcut = self.config.get_shortcut(action)
            widget.setKeySequence(QKeySequence(shortcut))
        
        # Load colors
        for color_name, preview in self.color_widgets.items():
            color = self.config.get_color(color_name)
            self.update_color_preview(color_name, color)
        
        # Load UI params
        self.ui_widgets["pan_step"].setValue(self.config.get_ui_param("pan_step"))
        zoom_factor = self.config.get_ui_param("zoom_factor")
        self.ui_widgets["zoom_factor"].setValue(int(zoom_factor * 100))
        self.ui_widgets["bbox_resize_margin"].setValue(self.config.get_ui_param("bbox_resize_margin"))
    
    def choose_color(self, color_name):
        """Open color picker dialog."""
        current_color = self.config.get_color(color_name)
        
        # For colors with alpha, use getRgba
        color = QColorDialog.getColor(
            current_color, 
            self, 
            f"Choisir couleur - {color_name}",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        
        if color.isValid():
            self.temp_colors[color_name] = color
            self.update_color_preview(color_name, color)
    
    def update_color_preview(self, color_name, color):
        """Update color preview label."""
        preview = self.color_widgets[color_name]
        
        # Set background color
        palette = preview.palette()
        palette.setColor(preview.backgroundRole(), color)
        preview.setPalette(palette)
        
        # Add border and display color values
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        preview.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({r}, {g}, {b}, {a});
                border: 2px solid #666666;
                border-radius: 4px;
            }}
        """)
        
        # Set tooltip with color information
        preview.setToolTip(f"RGBA: ({r}, {g}, {b}, {a})\nHex: {color.name()}")
    
    def accept_changes(self):
        """Apply and save all changes."""
        # Save shortcuts
        for action, widget in self.shortcut_widgets.items():
            sequence = widget.keySequence().toString()
            self.config.update_shortcut(action, sequence)
        
        # Save colors
        for color_name, color in self.temp_colors.items():
            self.config.update_color(color_name, color)
        
        # Save UI params
        self.config.update_ui_param("pan_step", self.ui_widgets["pan_step"].value())
        self.config.update_ui_param("zoom_factor", self.ui_widgets["zoom_factor"].value() / 100.0)
        self.config.update_ui_param("bbox_resize_margin", self.ui_widgets["bbox_resize_margin"].value())
        
        self.settings_changed.emit()
        self.accept()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Confirmer",
            "Voulez-vous vraiment rétablir les valeurs par défaut ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_current_settings()
            self.temp_colors.clear()
            self.temp_ui_params.clear()
            self.logger.info("Settings reset to defaults")
