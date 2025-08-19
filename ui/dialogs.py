# ui/dialogs.py
"""
Contém todas as classes de diálogo personalizadas para a aplicação,
como a visualização de dados e a seleção de datas.
"""

import pandas as pd
import qtawesome as qta
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QHBoxLayout, QPushButton,
    QDialogButtonBox, QComboBox, QLabel
)
from PySide6.QtCore import Qt

from ui.models import DataFrameTableModel


class PreviewDialog(QDialog):
    """
    Um diálogo que exibe um DataFrame do pandas em uma QTableView
    para permitir a visualização de dados de um arquivo CSV.
    """
    def __init__(self, df: pd.DataFrame, file_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Visualização de Dados - {file_name}")
        self.setWindowIcon(qta.icon('fa5s.table', color='#6a2e4d'))
        self.setObjectName("previewDialog")
        self.resize(900, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setWordWrap(False)
        self.table_view.setModel(DataFrameTableModel(df))
        main_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fechar")
        close_button.setObjectName("dialogButton")
        close_button.setMinimumWidth(120)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)


class MonthYearDialog(QDialog):
    """
    Um diálogo para que o usuário possa selecionar um mês e um ano
    de forma amigável, usando ComboBoxes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Competência")
        self.setWindowIcon(qta.icon('fa5s.calendar-alt', color='#6a2e4d'))
        self.setModal(True) # Impede interação com a janela principal
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        layout.addWidget(QLabel("Por favor, selecione o mês e o ano de referência:"))

        # Layout para os ComboBoxes
        combo_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.month_combo.setCursor(Qt.PointingHandCursor)
        self.year_combo = QComboBox()
        self.year_combo.setCursor(Qt.PointingHandCursor)
        
        combo_layout.addWidget(QLabel("Mês:"))
        combo_layout.addWidget(self.month_combo, 1) # O '1' é o fator de esticamento
        combo_layout.addSpacing(10)
        combo_layout.addWidget(QLabel("Ano:"))
        combo_layout.addWidget(self.year_combo, 1)
        layout.addLayout(combo_layout)

        # Populando os ComboBoxes
        self._populate_combos()

        # Botões OK e Cancelar (padrão do sistema)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Mapeamento de nome do mês para número
        self.month_map = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
            "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }

    def _populate_combos(self):
        """Preenche os combo boxes com meses e anos."""
        # Meses
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.month_combo.addItems(months)
        
        # Anos (últimos 5 anos + ano atual + próximo ano)
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 2)]
        self.year_combo.addItems(years)

        # Definir valores padrão para o mês e ano atuais para melhor UX
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.year_combo.setCurrentText(str(current_year))

    def get_selected_date(self):
        """
        Retorna uma tupla com o mês (int) e o ano (int) selecionados pelo usuário.
        """
        month_name = self.month_combo.currentText()
        year_str = self.year_combo.currentText()
        
        selected_month = self.month_map[month_name]
        selected_year = int(year_str)
        
        return selected_month, selected_year