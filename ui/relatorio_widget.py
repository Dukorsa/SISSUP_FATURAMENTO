import sys
import os
from datetime import datetime
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox, QFrame, QProgressBar, QDialog, QScrollArea, QComboBox
)
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QThread, QSize

import qtawesome as qta

from core.database import Database
from core.importer import ImportWorker

from core.reports import REPORT_REGISTRY
from core.exporter import export_simple_excel
from config import get_clean_headers, REPORT_DEFINITIONS, DATA_SOURCE_TITLES
from styles import COLORS
from ui.dialogs import PreviewDialog
from ui.flow_layout import FlowLayout

try:
    import openpyxl
    import reportlab
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False

class RelatorioWidget(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.cards = {}
        self.selected_clinic = None
        self.selected_month = None
        self.selected_year = None

        self.logo_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), '..', 'assets', 'logo.png')
        self.report_definitions = REPORT_DEFINITIONS
        self.data_source_titles = DATA_SOURCE_TITLES
        self._setup_ui()
        self._set_content_enabled(False) # Desabilita conteúdo na inicialização

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll_area)

        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)

        content_layout = QVBoxLayout(scroll_content_widget)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(25)
        
        params_section = self._create_parameters_section()
        content_layout.addWidget(params_section)
        
        content_layout.addWidget(self._create_section_header("1. Fontes de Dados (Importação)", icon_name='fa5s.database'))
        self.import_cards_container = QWidget()
        self.import_cards_layout = FlowLayout(self.import_cards_container)
        self.import_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.import_cards_layout.setSpacing(25)
        content_layout.addWidget(self.import_cards_container)

        content_layout.addWidget(self._create_section_header("2. Avisos", icon_name='fa5s.exclamation-triangle'))
        self.corrections_cards_container = QWidget()
        self.corrections_cards_layout = FlowLayout(self.corrections_cards_container)
        self.corrections_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.corrections_cards_layout.setSpacing(25)
        content_layout.addWidget(self.corrections_cards_container)

        content_layout.addWidget(self._create_section_header("3. Relatórios Gerados (Exportação)", icon_name='fa5s.file-export'))
        self.export_cards_container = QWidget()
        self.export_cards_layout = FlowLayout(self.export_cards_container)
        self.export_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.export_cards_layout.setSpacing(25)
        content_layout.addWidget(self.export_cards_container)
        content_layout.addStretch(1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setContentsMargins(30, 5, 30, 10)
        main_layout.addWidget(self.progress_bar)

        self._clear_layout(self.import_cards_layout)
        self._clear_layout(self.corrections_cards_layout)
        self._clear_layout(self.export_cards_layout)
        
    def _create_parameters_section(self):
        section_frame = QFrame()
        section_frame.setObjectName("parametersSection")
        layout = QVBoxLayout(section_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        layout.addWidget(self._create_section_header("Parâmetros do Relatório", icon_name='fa5s.filter'))

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Clínica:"))
        self.clinic_combo = QComboBox()
        self.clinic_combo.setCursor(Qt.PointingHandCursor)
        self.clinic_combo.addItems([
            "Selecione uma clínica...", "Renal Clínica", "Instituto do Rim", "Nefron Clínica",
            "CNN", "Pronto Rim", "Clínica do Rim", "Hospital do Rim"
        ])
        form_layout.addWidget(self.clinic_combo, 2)
        form_layout.addSpacing(20)

        form_layout.addWidget(QLabel("Período de Referência:"))
        self.month_combo = QComboBox()
        self.month_combo.setCursor(Qt.PointingHandCursor)
        self.year_combo = QComboBox()
        self.year_combo.setCursor(Qt.PointingHandCursor)
        self._populate_date_combos()
        form_layout.addWidget(self.month_combo, 1)
        form_layout.addWidget(self.year_combo, 1)

        form_layout.addStretch(2)

        self.apply_button = QPushButton(qta.icon('fa5s.check-circle', color='white'), " Aplicar Parâmetros")
        self.apply_button.setObjectName("primaryButton")
        self.apply_button.setCursor(Qt.PointingHandCursor)
        self.apply_button.clicked.connect(self._on_apply_filters)
        form_layout.addWidget(self.apply_button)
        
        layout.addLayout(form_layout)
        return section_frame
        
    def _populate_date_combos(self):
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.month_combo.addItems(months)
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 2)]
        self.year_combo.addItems(years)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.year_combo.setCurrentText(str(current_year))

    def _set_content_enabled(self, enabled: bool):
        self.import_cards_container.setEnabled(enabled)
        self.corrections_cards_container.setEnabled(enabled)
        self.export_cards_container.setEnabled(enabled)

        opacity = 1.0 if enabled else 0.5
        style = f"QFrame#card {{ opacity: {opacity}; }}"
        self.import_cards_container.setStyleSheet(style)
        self.corrections_cards_container.setStyleSheet(style)
        self.export_cards_container.setStyleSheet(style)
        
    def _on_apply_filters(self):
        clinic_index = self.clinic_combo.currentIndex()
        if clinic_index == 0:
            QMessageBox.warning(self, "Seleção Incompleta", "Por favor, selecione uma clínica para continuar.")
            return

        self.selected_clinic = self.clinic_combo.currentText()
        month_name = self.month_combo.currentText()
        year_str = self.year_combo.currentText()
        
        month_map = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
            "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }
        self.selected_month = month_map[month_name]
        self.selected_year = int(year_str)

        QMessageBox.information(self, "Parâmetros Definidos", 
            f"Relatórios para:\n\nClínica: {self.selected_clinic}\nPeríodo: {self.selected_month:02d}/{self.selected_year}"
        )
        self._set_content_enabled(True)

    def load_report_data(self, report_name):
        self.update_report_view(report_name)
        self.clinic_combo.setCurrentIndex(0)
        self._set_content_enabled(False)
        self.selected_clinic = None
        self.selected_month = None
        self.selected_year = None

    def update_report_view(self, report_name):
        report_config = self.report_definitions.get(report_name, {})
        self._clear_layout(self.import_cards_layout)
        for table_name in report_config.get("imports", []):
            title = self.data_source_titles.get(table_name, table_name)
            self._create_import_card(self.import_cards_layout, title, table_name)
        self._clear_layout(self.corrections_cards_layout)
        for correction_name in report_config.get("corrections", []):
            self._create_correction_card(self.corrections_cards_layout, correction_name)
        self.update_correction_cards()
        self._clear_layout(self.export_cards_layout)
        for export_name in report_config.get("exports", []):
            self._create_export_card(self.export_cards_layout, export_name)

    def _create_import_card(self, p_layout, title_text, t_name):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        info = QLabel("Nenhuma importação registrada.")
        info.setObjectName("infoLabel")
        layout.addWidget(info)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_preview = QPushButton(qta.icon('fa5s.eye', color=COLORS['icon-color-light-bg']), " Visualizar")
        btn_preview.setObjectName("previewButton")
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.clicked.connect(lambda: self.select_and_preview(t_name))
        btn_layout.addWidget(btn_preview)
        btn_import = QPushButton(qta.icon('fa5s.upload', color=COLORS['icon-color-dark-bg']), " Importar")
        btn_import.setObjectName("importButton")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.clicked.connect(lambda: self.select_and_import(t_name))
        btn_layout.addWidget(btn_import)
        layout.addLayout(btn_layout)
        p_layout.addWidget(card)
        self.cards[t_name] = {'info_label': info}
        self.update_card_info(t_name)

    def _create_correction_card(self, p_layout, title_text):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        count_layout = QHBoxLayout()
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.addWidget(QLabel("Total:"))
        self.remarcacoes_count_label = QLabel("0")
        self.remarcacoes_count_label.setObjectName("countLabel")
        count_layout.addWidget(self.remarcacoes_count_label)
        count_layout.addStretch()
        layout.addLayout(count_layout)
        layout.addStretch()
        btn_excel = QPushButton(qta.icon('fa5s.file-excel', color=COLORS['icon-color-light-bg']), " Exportar para Excel")
        self.remarcacoes_export_button = btn_excel
        self.remarcacoes_export_button.setObjectName("exportButton")
        self.remarcacoes_export_button.setCursor(Qt.PointingHandCursor)
        self.remarcacoes_export_button.clicked.connect(self.on_export_remarcacoes_clicked)
        layout.addWidget(self.remarcacoes_export_button)
        p_layout.addWidget(card)

    def _create_export_card(self, p_layout, title_text):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_excel = QPushButton(qta.icon('fa5s.file-excel', color=COLORS['icon-color-light-bg']), " Excel")
        btn_excel.setObjectName("exportButton")
        btn_excel.setCursor(Qt.PointingHandCursor)
        btn_excel.clicked.connect(lambda: self.on_export_clicked(title_text, "Excel"))
        btn_layout.addWidget(btn_excel)
        btn_pdf = QPushButton(qta.icon('fa5s.file-pdf', color=COLORS['icon-color-light-bg']), " PDF")
        btn_pdf.setObjectName("exportButton")
        btn_pdf.setCursor(Qt.PointingHandCursor)
        btn_pdf.clicked.connect(lambda: self.on_export_clicked(title_text, "PDF"))
        btn_layout.addWidget(btn_pdf)
        layout.addLayout(btn_layout)
        p_layout.addWidget(card)

    def select_and_import(self, table_name):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Importar CSV para {self.data_source_titles.get(table_name, table_name)}", "", "Arquivos CSV (*.csv)")
        if not file_path: return
        try:
            clean_headers = get_clean_headers(table_name)
            df_preview = pd.read_csv(file_path, sep=';', encoding='latin-1', header=None, skiprows=1, dtype=str)
            if len(df_preview.columns) != len(clean_headers):
                QMessageBox.warning(self, "Erro de Colunas", f"O arquivo possui {len(df_preview.columns)} colunas, mas são esperadas {len(clean_headers)}.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Ler CSV", str(e))
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Importação")
        msg_box.setText(f"<b>Arquivo:</b> {os.path.basename(file_path)}\n<b>Total de linhas:</b> {len(df_preview)}\n\nIsso substituirá todos os dados existentes. Deseja continuar?")
        if msg_box.exec() != QMessageBox.StandardButton.Ok: return
        self._current_import_context = {"table_name": table_name}
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.thread = QThread()
        self.worker = ImportWorker(self.db, file_path, table_name)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_import_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_import_finished(self, ok, message):
        self.progress_bar.setVisible(False)
        if not hasattr(self, '_current_import_context') or not self._current_import_context: return
        if not ok:
            QMessageBox.critical(self, "Erro na Importação", message)
        else:
            QMessageBox.information(self, "Sucesso", message)
        table_name = self._current_import_context["table_name"]
        self.update_card_info(table_name)
        if table_name == 'sessoes_hd':
            self.update_correction_cards()
        self._current_import_context = None

    def on_export_clicked(self, report_name, file_format):
        if not all([self.selected_clinic, self.selected_month, self.selected_year]):
            QMessageBox.critical(self, "Parâmetros Ausentes", "Por favor, selecione a clínica e o período e clique em 'Aplicar Parâmetros' antes de exportar.")
            return

        if not LIBS_AVAILABLE:
            QMessageBox.critical(self, "Bibliotecas Ausentes", "As bibliotecas 'openpyxl' e 'reportlab' são necessárias para exportar.")
            return

        report_class = REPORT_REGISTRY.get(report_name)
        if not report_class:
            QMessageBox.information(self, "Funcionalidade Futura", f"A exportação para '{report_name}' ainda não foi implementada.")
            return

        required_tables = self.report_definitions["Relatório de Fechamento SUS"]["imports"]
        if any(self.db.get_last_import_info(tbl) is None for tbl in required_tables):
            missing = [self.data_source_titles[tbl] for tbl in required_tables if self.db.get_last_import_info(tbl) is None]
            QMessageBox.critical(self, "Fontes de Dados Ausentes", f"Por favor, importe os dados para: {', '.join(missing)}")
            return

        try:
            self.setCursor(QCursor(Qt.WaitCursor))

            report_params = {
                'clinic': self.selected_clinic,
                'month': self.selected_month,
                'year': self.selected_year
            }
            
            report_instance = report_class(self.db, self.logo_path, **report_params)

            file_filter = f"Arquivo {file_format} (*.{'xlsx' if file_format == 'Excel' else 'pdf'})"
            
            safe_title = report_instance.title.replace('/', '-').replace('\\', '-')
            default_filename = f"{safe_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
            
            file_path, _ = QFileDialog.getSaveFileName(self, f"Salvar {report_instance.title}", default_filename, file_filter)

            if not file_path:
                self.unsetCursor()
                return

            report_instance.export(file_path, file_format)

            QMessageBox.information(self, "Exportação Concluída", f"O relatório '{report_instance.title}' foi salvo com sucesso.")

        except ValueError as ve:
            QMessageBox.information(self, "Nenhum Resultado", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Ocorreu um erro ao gerar ou salvar o relatório:\n\n{str(e)}")
        finally:
            self.unsetCursor()

    def _create_section_header(self, text, icon_name='fa5s.caret-right'):
        header_frame = QFrame()
        header_frame.setObjectName("sectionHeaderFrame")
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        if icon_name:
            icon = QLabel()
            icon.setPixmap(qta.icon(icon_name, color=COLORS['primary']).pixmap(QSize(18, 18)))
            layout.addWidget(icon)
        title = QLabel(text)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addStretch()
        return header_frame

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_correction_cards(self):
        if hasattr(self, 'remarcacoes_count_label'):
            remarcacoes_count = self.db.get_remarcacoes_count()
            self.remarcacoes_count_label.setText(str(remarcacoes_count))
            if remarcacoes_count > 0:
                self.remarcacoes_export_button.setEnabled(True)
                self.remarcacoes_export_button.setToolTip("Exportar a lista de pacientes com sessões remarcadas.")
            else:
                self.remarcacoes_export_button.setEnabled(False)
                self.remarcacoes_export_button.setToolTip("Não há remarcações para exportar.")

    def on_export_remarcacoes_clicked(self):
        if not self.db.get_last_import_info('sessoes_hd'):
            QMessageBox.warning(self, "Fonte de Dados Ausente", "Por favor, importe o arquivo de 'Sessões HD (p/ Remarcações)' primeiro.")
            return
        try:
            self.setCursor(QCursor(Qt.WaitCursor))
            df_remarcacoes = self.db.get_remarcacoes_data()
            if df_remarcacoes.empty:
                QMessageBox.information(self, "Nenhum Resultado", "Não foram encontrados dados de remarcações para exportar.")
                self.unsetCursor()
                return
            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório de Remarcações", "relatorio_remarcacoes", "Arquivo Excel (*.xlsx)")
            if not file_path:
                self.unsetCursor()
                return
            export_simple_excel(df_remarcacoes, file_path, sheet_name="Remarcações")
            QMessageBox.information(self, "Exportação Concluída", "O relatório de remarcações foi salvo com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Ocorreu um erro ao exportar as remarcações: {str(e)}")
        finally:
            self.unsetCursor()

    def update_card_info(self, table_name):
        info_data = self.db.get_last_import_info(table_name)
        info_label = self.cards.get(table_name, {}).get('info_label')
        if info_label:
            if info_data:
                info_label.setText(f"<b>Última:</b> {datetime.fromisoformat(info_data['data_importacao']).strftime('%d/%m/%Y às %H:%M')}<br><b>Linhas:</b> {info_data['linhas']}")
            else:
                info_label.setText("Nenhuma importação registrada.")

    def select_and_preview(self, table_name):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Visualizar CSV para {self.data_source_titles.get(table_name, table_name)}", "", "Arquivos CSV (*.csv)")
        if not file_path: return
        try:
            clean_headers = get_clean_headers(table_name)
            df = pd.read_csv(file_path, sep=';', encoding='latin-1', header=None, skiprows=1, dtype=str)
            if len(df.columns) != len(clean_headers):
                QMessageBox.warning(self, "Erro de Colunas", f"O arquivo possui {len(df.columns)} colunas, mas são esperadas {len(clean_headers)}.")
                return
            df.columns = clean_headers
            dialog = PreviewDialog(df, os.path.basename(file_path), self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Ler CSV", str(e))