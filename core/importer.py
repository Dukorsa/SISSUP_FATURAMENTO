# core/importer.py
from PySide6.QtCore import QObject, Signal, Slot
from core.database import Database

class ImportWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(int)
    
    def __init__(self, db: Database, file_path: str, table_name: str):
        super().__init__()
        self.db = db
        self.file_path = file_path
        self.table_name = table_name
        
    @Slot()
    def run(self):
        try:
            self.progress.emit(10)
            result = self.db.import_from_csv(self.file_path, self.table_name)
            self.progress.emit(100)
            msg = "Importação concluída com sucesso." if result else "Arquivo processado, mas não continha linhas válidas."
            self.finished.emit(result, msg)
        except Exception as e:
            self.finished.emit(False, str(e))