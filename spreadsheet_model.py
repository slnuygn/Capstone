from PyQt6.QtCore import QAbstractTableModel, Qt, pyqtSignal, QVariant, QModelIndex
from PyQt6.QtQml import qmlRegisterType
import numpy as np

class SpreadsheetModel(QAbstractTableModel):
    """
    A table model for displaying data in a spreadsheet-like format
    Supports scalars, 1D arrays, 2D arrays, and higher dimensional arrays
    """
    
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = []
        self._rows = 0
        self._cols = 0
        self._original_shape = None
        
    def setSpreadsheetData(self, data_array, headers=None):
        """Set the spreadsheet data from numpy array or list"""
        try:
            self.beginResetModel()
            
            print(f"DEBUG: Setting spreadsheet data, type: {type(data_array)}")
            
            # Handle None or empty data
            if data_array is None:
                self._data = []
                self._rows, self._cols = 0, 0
                self.endResetModel()
                return
                
            # Convert to numpy array if not already
            if not isinstance(data_array, np.ndarray):
                if isinstance(data_array, (list, tuple)):
                    data_array = np.array(data_array)
                else:
                    # Single scalar value
                    data_array = np.array([data_array])
                    
            self._original_shape = data_array.shape
            print(f"DEBUG: Original data shape: {self._original_shape}")
            
            # Handle different dimensions
            if data_array.ndim == 0:  # Scalar
                self._data = [[str(data_array.item())]]
                self._rows, self._cols = 1, 1
                print("DEBUG: Processed as scalar")
                
            elif data_array.ndim == 1:  # 1D array
                self._data = [[str(item)] for item in data_array]
                self._rows, self._cols = len(data_array), 1
                print(f"DEBUG: Processed as 1D array: {self._rows} rows")
                
            elif data_array.ndim == 2:  # 2D array
                self._data = [[str(item) for item in row] for row in data_array]
                self._rows, self._cols = data_array.shape
                print(f"DEBUG: Processed as 2D array: {self._rows}x{self._cols}")
                
            else:  # Higher dimensions - flatten to 2D
                # Reshape to 2D keeping last dimension
                if data_array.size > 1000:  # Limit for performance
                    print("DEBUG: Large array detected, showing first 1000 elements")
                    flat_data = data_array.flatten()[:1000]
                    reshaped = flat_data.reshape(-1, 1)
                else:
                    reshaped = data_array.reshape(-1, data_array.shape[-1] if data_array.shape[-1] > 1 else 1)
                    
                self._data = [[str(item) for item in row] for row in reshaped]
                self._rows, self._cols = reshaped.shape
                print(f"DEBUG: Processed as higher-dim array, reshaped to: {self._rows}x{self._cols}")
                
            # Set column headers
            if headers and len(headers) >= self._cols:
                self._headers = headers[:self._cols]
            else:
                self._headers = [f"Column {i+1}" for i in range(self._cols)]
                
            print(f"DEBUG: Final spreadsheet dimensions: {self._rows} rows, {self._cols} columns")
            
            self.endResetModel()
            self.dataChanged.emit()
            
        except Exception as e:
            print(f"ERROR: Failed to set spreadsheet data: {e}")
            import traceback
            traceback.print_exc()
            
            # Set empty data on error
            self._data = []
            self._rows, self._cols = 0, 0
            self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        return self._rows
        
    def columnCount(self, parent=QModelIndex()):
        return self._cols
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= self._rows or index.column() >= self._cols:
            return QVariant()
            
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                return self._data[index.row()][index.column()]
            except (IndexError, TypeError):
                return ""
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
            
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._headers):
                    return self._headers[section]
                else:
                    return f"Col {section+1}"
            else:
                return str(section + 1)  # Row numbers starting from 1
        return QVariant()
        
    def clearData(self):
        """Clear all data from the model"""
        self.beginResetModel()
        self._data = []
        self._headers = []
        self._rows = 0
        self._cols = 0
        self._original_shape = None
        self.endResetModel()
        self.dataChanged.emit()

# Register the type for QML usage
def register_spreadsheet_model():
    qmlRegisterType(SpreadsheetModel, "SpreadsheetComponents", 1, 0, "SpreadsheetModel")
