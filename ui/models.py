# ui/models.py
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.reset_index(drop=True)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        if orientation == Qt.Horizontal: return str(self._df.columns[section])
        return str(section + 1)

    def rowCount(self, parent=QModelIndex()): return len(self._df.index)
    def columnCount(self, parent=QModelIndex()): return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole: return None
        val = self._df.iat[index.row(), index.column()]
        return "" if pd.isna(val) else str(val)

    def set_dataframe(self, df):
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()