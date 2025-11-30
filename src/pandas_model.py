from PySide6.QtCore import QAbstractTableModel, Qt
import pandas as pd

from PySide6.QtGui import QColor
from src.config_manager import ConfigManager

class PandasModel(QAbstractTableModel):
    def __init__(self, data_model):
        super().__init__()
        self.data_model = data_model
        self._data = data_model.df

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                val = self._data.iloc[index.row(), index.column()]
                if pd.isna(val):
                    return ""
                return str(val)
            
            if role == Qt.ItemDataRole.BackgroundRole:
                if self.data_model.is_modified(index.row(), index.column()):
                    return ConfigManager().get_color('modified_cell_bg')
                    
        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            # self._data.iloc[index.row(), index.column()] = value
            self.data_model.update_cell(index.row(), index.column(), value)
            self.dataChanged.emit(index, index, [role, Qt.ItemDataRole.BackgroundRole])
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
