import json
import os
import logging
from PySide6.QtGui import QColor

class ConfigManager:
    """
    Singleton class to manage application configuration.
    Handles loading, saving, and accessing configuration parameters.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self.config_path = "config.json"
        self.config = self.load_config()
    
    def get_default_config(self):
        """Returns the default configuration."""
        return {
            "shortcuts": {
                "zoom_in": "=",
                "zoom_out": "-",
                "zoom_reset": "R",
                "pan_up": "Z",
                "pan_down": "S",
                "pan_left": "Q",
                "pan_right": "D",
                "create_bbox": "N",
                "undo": "Ctrl+Z",
                "toggle_calibration": "C"
            },
            "colors": {
                "bbox_border": [255, 0, 0, 128],
                "bbox_fill": [255, 0, 0, 30],
                "modified_cell_bg": [180, 100, 40],
                "background": "#2b2b2b",
                "button_primary": "#007acc",
                "button_hover": "#0098ff",
                "button_pressed": "#005c99",
                "button_checked": "#005c99"
            },
            "ui": {
                "pan_step": 50,
                "zoom_factor": 1.2,
                "bbox_resize_margin": 10
            },
            "api": {
                "gemini_api_key": "",
                "download_directory": "downloaded_images"
            }
        }
    
    def load_config(self):
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                
                # Merge with defaults to ensure all keys exist
                default = self.get_default_config()
                for section in default:
                    if section not in config:
                        config[section] = default[section]
                    else:
                        for key in default[section]:
                            if key not in config[section]:
                                config[section][key] = default[section][key]
                
                return config
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}. Using defaults.")
                return self.get_default_config()
        else:
            self.logger.info("Config file not found. Creating default configuration.")
            config = self.get_default_config()
            self.save_config()
            return config
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get_shortcut(self, action):
        """Get shortcut string for an action."""
        return self.config.get("shortcuts", {}).get(action, "")
    
    def get_color(self, name):
        """Get QColor for a color name."""
        color_value = self.config.get("colors", {}).get(name)
        
        if isinstance(color_value, list):
            # RGBA list format
            if len(color_value) == 3:
                return QColor(*color_value)
            elif len(color_value) == 4:
                return QColor(*color_value)
        elif isinstance(color_value, str):
            # Hex string format
            return QColor(color_value)
        
        # Fallback
        return QColor(255, 255, 255)
    
    def get_ui_param(self, name):
        """Get UI parameter value."""
        return self.config.get("ui", {}).get(name, 0)
    
    def update_shortcut(self, action, shortcut):
        """Update a shortcut and save config."""
        if "shortcuts" not in self.config:
            self.config["shortcuts"] = {}
        self.config["shortcuts"][action] = shortcut
        self.save_config()
    
    def update_color(self, name, color):
        """Update a color and save config."""
        if "colors" not in self.config:
            self.config["colors"] = {}
        
        # Store as RGBA list
        if isinstance(color, QColor):
            self.config["colors"][name] = [color.red(), color.green(), color.blue(), color.alpha()]
        elif isinstance(color, str):
            self.config["colors"][name] = color
        
        self.save_config()
    
    def update_ui_param(self, name, value):
        """Update a UI parameter and save config."""
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"][name] = value
        self.save_config()
    
    def get_api_key(self):
        """Get Gemini API key."""
        return self.config.get("api", {}).get("gemini_api_key", "")
    
    def set_api_key(self, api_key):
        """Set Gemini API key."""
        if "api" not in self.config:
            self.config["api"] = {}
        self.config["api"]["gemini_api_key"] = api_key
        self.save_config()
    
    def get_download_directory(self):
        """Get download directory."""
        return self.config.get("api", {}).get("download_directory", "downloaded_images")
    
    def set_download_directory(self, directory):
        """Set download directory."""
        if "api" not in self.config:
            self.config["api"] = {}
        self.config["api"]["download_directory"] = directory
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.get_default_config()
        self.save_config()
        self.logger.info("Configuration reset to defaults")
