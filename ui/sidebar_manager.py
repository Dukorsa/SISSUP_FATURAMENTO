# --- INÍCIO DO ARQUIVO COMPLETO E CORRIGIDO: ui/sidebar_manager.py ---

import qtawesome as qta
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from PySide6.QtCore import QObject, Signal, Slot, Qt

class SidebarManager(QObject):
    """
    Gerencia um QTreeWidget como um menu lateral, populando-o a partir de uma
    configuração e emitindo um sinal quando um módulo selecionável é clicado.
    """
    module_selected = Signal(dict)

    def __init__(self, tree_widget: QTreeWidget, sidebar_config: list, parent: QObject = None):
        super().__init__(parent)
        self.tree_widget = tree_widget
        self.sidebar_config = sidebar_config
        self._setup_tree_widget()
        self.tree_widget.itemClicked.connect(self._on_item_clicked)

    def _setup_tree_widget(self):
        """Configura as propriedades e o estilo base do QTreeWidget."""
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setObjectName("menuTree")
        self.tree_widget.setIndentation(15)
        self.tree_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree_widget.setAnimated(True)
        self.tree_widget.setExpandsOnDoubleClick(False)

    def populate_sidebar(self):
        """Popula a barra lateral com base na lista de configuração."""
        self.tree_widget.clear()
        for item_config in self.sidebar_config:
            if item_config.get("is_group", False):
                group_item = self._create_group_item(item_config)
                self.tree_widget.addTopLevelItem(group_item)
                group_item.setExpanded(True) # Grupos começam expandidos
            else:
                self._create_module_item(item_config, self.tree_widget)

    def _create_group_item(self, config: dict) -> QTreeWidgetItem:
        """Cria um item de grupo (pai) para a barra lateral."""
        group_item = QTreeWidgetItem()
        group_item.setText(0, config.get("name", "Grupo"))
        if "icon" in config:
            group_item.setIcon(0, qta.icon(config["icon"], color='white'))
        group_item.setData(0, Qt.ItemDataRole.UserRole, config)
        for module_config in config.get("modules", []):
            self._create_module_item(module_config, group_item)
        return group_item

    def _create_module_item(self, config: dict, parent_item: QTreeWidget | QTreeWidgetItem):
        """Cria um item de módulo (filho ou nível superior)."""
        module_item = QTreeWidgetItem(parent_item)
        module_item.setText(0, config.get("text", "Módulo"))
        
        # Lógica corrigida para adicionar ícone a qualquer módulo que o defina
        if "icon" in config:
             module_item.setIcon(0, qta.icon(config["icon"], color='white'))
        
        module_item.setData(0, Qt.ItemDataRole.UserRole, config)
        return module_item

    @Slot(QTreeWidgetItem, int)
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Slot ativado quando qualquer item é clicado.
        Expande/recolhe se for um grupo, ou emite sinal se for um módulo.
        """
        item_data = item.data(column, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        if item_data.get("is_group", False):
            item.setExpanded(not item.isExpanded())
            return
        
        self.module_selected.emit(item_data)
        
    def select_initial_item(self):
        """Encontra e seleciona o primeiro item de nível superior (geralmente "Início")."""
        if self.tree_widget.topLevelItemCount() > 0:
            initial_item = self.tree_widget.topLevelItem(0)
            self.tree_widget.setCurrentItem(initial_item)
            initial_data = initial_item.data(0, Qt.ItemDataRole.UserRole)
            if initial_data:
                self.module_selected.emit(initial_data)
    
    def select_item_by_id(self, item_id: str):
        """ Encontra e seleciona um item do menu com base em seu ID. """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get("id") == item_id:
                if item.parent():
                    item.parent().setExpanded(True)
                
                self.tree_widget.setCurrentItem(item)
                self._on_item_clicked(item, 0) # Emite o sinal como se o usuário tivesse clicado
                return
            iterator += 1