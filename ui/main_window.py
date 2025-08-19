# --- INÍCIO DO ARQUIVO COMPLETO E CORRIGIDO: ui/main_window.py ---

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QTreeWidget, QTreeWidgetItemIterator,
    QGraphicsColorizeEffect
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QIcon, QCursor, QPixmap, QResizeEvent, QColor
from PySide6.QtCore import Qt, Slot, QSize, QPropertyAnimation, QEasingCurve, QRect, QEvent, QTimer

import qtawesome as qta

from core.database import Database
from ui.relatorio_widget import RelatorioWidget
from ui.sidebar_manager import SidebarManager
from config import SIDEBAR_CONFIG
from core.utils import resource_path
from styles import COLORS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.logo_path = resource_path('assets/logo.png')
        self.setWindowTitle("Grupo Nefron - Sistema de Análise")
        app_icon_path = resource_path('assets/logo.ico')
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))
        self.resize(1280, 850)
        self._sidebar_width = 260
        self._sidebar_visible = False
        self._sidebar_animation_duration = 250
        self._setup_base_ui_structure()
        self._setup_sidebar_manager()
        self._setup_sidebar_animation()
        self._connect_signals()
        self.sidebar_manager.select_initial_item()
        self.showMaximized()

    def _create_report_lobby_card(self, title, description, icon_name, item_id):
        card = QFrame()
        card.setObjectName("lobbyCard")
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        layout.addStretch()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=COLORS['primary']).pixmap(QSize(48, 48)))
        icon_label.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setObjectName("lobbyCardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        description_label = QLabel(description)
        description_label.setObjectName("lobbyCardText")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
        card.mousePressEvent = lambda event: self.sidebar_manager.select_item_by_id(item_id)
        return card

    def _create_home_page(self):
        page = QWidget()
        page.setObjectName("homePage")
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_container = QFrame()
        top_container.setObjectName("homeTopContainer")
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(40, 40, 40, 40)
        top_layout.setSpacing(25)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.home", color=COLORS['primary']).pixmap(QSize(64, 64)))
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        title_label = QLabel("Bem-vindo(a) ao SISSUP")
        title_label.setObjectName("welcomeTitle")
        subtitle_label = QLabel("Seu assistente para análise e geração de relatórios de faturamento.")
        subtitle_label.setObjectName("welcomeText")
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        
        top_layout.addWidget(icon_label)
        top_layout.addLayout(text_layout)
        top_layout.addStretch()

        # --- CÓDIGO DA ASSINATURA REINSERIDO AQUI ---
        signature_path = resource_path('assets/assinatura.svg')
        if os.path.exists(signature_path):
            signature_widget = QSvgWidget(signature_path)
            signature_widget.setObjectName("signatureWidget")
            signature_widget.setFixedSize(120, 60)
            colorize_effect = QGraphicsColorizeEffect()
            colorize_effect.setColor(QColor(COLORS['text-muted']))
            signature_widget.setGraphicsEffect(colorize_effect)
            top_layout.addWidget(signature_widget)
        # --- FIM DO CÓDIGO DA ASSINATURA ---
        
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(40, 30, 40, 40)
        bottom_layout.setSpacing(15)
        lobby_title = QLabel("Módulos Disponíveis")
        lobby_title.setObjectName("lobbyTitle")
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(25)
        card_sus = self._create_report_lobby_card(
            title="Fechamento SUS",
            description="Importe dados e gere relatórios consolidados para o faturamento do SUS.",
            icon_name="fa5s.file-invoice-dollar",
            item_id="report_sus_closing"
        )
        cards_layout.addWidget(card_sus)
        cards_layout.addStretch()
        bottom_layout.addWidget(lobby_title)
        bottom_layout.addLayout(cards_layout)
        bottom_layout.addStretch()
        main_layout.addWidget(top_container)
        main_layout.addWidget(bottom_container)
        return page

    def _create_placeholder_page(self, title, msg, icon='fa5s.wrench'):
        page = QWidget()
        page.setObjectName("placeholderPage")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel()
        qta_icon = qta.icon(icon, color='#bdc3c7')
        pixmap = qta_icon.pixmap(QSize(128, 128))
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setObjectName("placeholderTitle")
        title_label.setAlignment(Qt.AlignCenter)
        message_label = QLabel(msg)
        message_label.setObjectName("placeholderMessage")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        return page

    def _setup_base_ui_structure(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(10, 0, 20, 0)
        top_bar_layout.setSpacing(10)
        self.menu_toggle_btn = QPushButton(qta.icon('fa5s.bars', color='white', scale_factor=1.2), "")
        self.menu_toggle_btn.setObjectName("menuToggleButton")
        self.menu_toggle_btn.setCursor(Qt.PointingHandCursor)
        top_bar_layout.addWidget(self.menu_toggle_btn)
        self.module_icon_label = QLabel()
        self.module_icon_label.hide()
        self.module_title_label = QLabel("Início")
        self.module_title_label.setObjectName("moduleTitle")
        top_bar_layout.addWidget(self.module_icon_label)
        top_bar_layout.addWidget(self.module_title_label)
        top_bar_layout.addStretch()
        self.main_layout.addWidget(self.top_bar)
        self.content_area = QWidget()
        self.content_area.setObjectName("mainContentArea")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_stack = QStackedWidget()
        self.home_page = self._create_home_page()
        self.relatorio_page = RelatorioWidget(self.db)
        self.settings_page = self._create_placeholder_page("Configurações", "Página para futuras configurações.", icon='fa5s.cog')
        self.widget_map = {
            "home_page": self.home_page,
            "relatorio_page": self.relatorio_page,
            "settings_page": self.settings_page,
        }
        for widget in self.widget_map.values():
            self.content_stack.addWidget(widget)
        content_layout.addWidget(self.content_stack)
        self.main_layout.addWidget(self.content_area, 1)
        self.content_overlay = QWidget(self)
        self.content_overlay.setObjectName("contentOverlay")
        self.content_overlay.hide()
        self.content_overlay.installEventFilter(self)
        self.sidebar_frame = QFrame(self)
        self.sidebar_frame.setObjectName("sidebar")
        self.sidebar_frame.setFixedWidth(self._sidebar_width)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10, 15, 10, 10)
        sidebar_layout.setSpacing(15)
        logo = QLabel()
        if os.path.exists(self.logo_path):
            logo.setPixmap(QPixmap(self.logo_path).scaledToWidth(180, Qt.SmoothTransformation))
        else:
            logo.setText("Grupo Nefron")
            logo.setObjectName("logoText")
        logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo)
        separator = QFrame(self)
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(separator)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setCursor(Qt.PointingHandCursor)
        sidebar_layout.addWidget(self.tree_widget, 1)
        sidebar_layout.addStretch()
        quit_btn = QPushButton(qta.icon('fa5s.sign-out-alt', color='white'), " Sair")
        quit_btn.setObjectName("quitButton")
        quit_btn.setCursor(Qt.PointingHandCursor)
        quit_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(quit_btn)
        self.sidebar_frame.move(-self._sidebar_width, self.top_bar.height())

    def _setup_sidebar_manager(self):
        self.sidebar_manager = SidebarManager(self.tree_widget, SIDEBAR_CONFIG, self)
        self.sidebar_manager.populate_sidebar()

    def _setup_sidebar_animation(self):
        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"geometry", self)
        self.sidebar_animation.setDuration(self._sidebar_animation_duration)
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutCubic)

    def _connect_signals(self):
        self.menu_toggle_btn.clicked.connect(self._toggle_sidebar)
        self.sidebar_manager.module_selected.connect(self.on_module_selected)

    @Slot()
    def _toggle_sidebar(self):
        y = self.top_bar.height()
        h = self.height() - y
        start_geo = self.sidebar_frame.geometry()
        if not self._sidebar_visible:
            end_geo = QRect(0, y, self._sidebar_width, h)
            self.content_overlay.show()
            self.content_overlay.raise_()
            self.sidebar_frame.raise_()
        else:
            end_geo = QRect(-self._sidebar_width, y, self._sidebar_width, h)
            self.content_overlay.hide()
        self.sidebar_animation.setStartValue(start_geo)
        self.sidebar_animation.setEndValue(end_geo)
        self.sidebar_animation.start()
        self._sidebar_visible = not self._sidebar_visible

    @Slot(dict)
    def on_module_selected(self, module_data: dict):
        widget_name = module_data.get("widget_name")
        widget_to_show = self.widget_map.get(widget_name)
        if widget_to_show:
            self.content_stack.setCurrentWidget(widget_to_show)
            title = module_data.get("text", "Início")
            current_item = self.tree_widget.currentItem()
            if current_item and current_item.parent():
                parent_text = current_item.parent().text(0)
                self.module_title_label.setText(f"{parent_text} / {title}")
            else:
                self.module_title_label.setText(title)
            icon_name = None
            if module_data.get("id") == "home":
                icon_name = "fa5s.home"
            elif module_data.get("report_name") == "Relatório de Fechamento SUS":
                icon_name = "fa5s.file-invoice-dollar"
            if icon_name:
                self.module_icon_label.setPixmap(qta.icon(icon_name, color='white').pixmap(QSize(18, 18)))
                self.module_icon_label.show()
            else:
                self.module_icon_label.hide()
            if widget_name == "relatorio_page" and module_data.get("report_name"):
                self.relatorio_page.load_report_data(module_data.get("report_name"))
            if self._sidebar_visible:
                QTimer.singleShot(50, self._toggle_sidebar)
        else:
            print(f"Aviso: Widget com nome '{widget_name}' não encontrado no widget_map.")
    
    def eventFilter(self, watched, event):
        if watched == self.content_overlay and event.type() == QEvent.MouseButtonPress and self._sidebar_visible:
            self._toggle_sidebar()
            return True
        return super().eventFilter(watched, event)