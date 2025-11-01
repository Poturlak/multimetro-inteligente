# -*- coding: utf-8 -*-
"""
MainWindow - Janela principal do Multímetro Inteligente v1.0
Integrada com ImageViewer real e todas as funcionalidades.
VERSÃO COMPLETA - Parte 1/2
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QStackedWidget, QFrame, QSplitter, QLabel, QMessageBox,
    QFileDialog, QToolBar, QMenuBar, QStatusBar, QPushButton,
    QButtonGroup, QDoubleSpinBox, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSlot
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QCloseEvent, QKeyEvent, QAction

# Imports do sistema
from src.views.image_viewer import ImageViewer
from src.views.points_table import PointsTableView
from src.controllers.state_manager import StateManager, AppState
from src.controllers.point_manager import PointManager
from src.models.project import BoardProject
from src.models.point import Point
from src.processing.persistence import ProjectPersistence


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação Multímetro Inteligente.
    
    Funcionalidades:
    - Carregamento e visualização de imagens de placas
    - Marcação de pontos de medição
    - Integração com multímetro via hardware
    - Comparação com tolerâncias
    - Salvamento de projetos .mip
    """
    
    def __init__(self):
        super().__init__()
        
        # Estado da aplicação
        self.project: Optional[BoardProject] = None
        self.current_file_path: Optional[str] = None
        self.has_unsaved_changes = False
        
        # Configurações
        self.settings = QSettings("MultimetroInteligente", "v1.0")
        
        # Controladores
        self.state_manager = StateManager()
        self.point_manager = PointManager()
        
        # Configurações de pontos
        self.current_shape = "circle"
        self.current_radius = 20
        self.current_width = 20
        self.current_height = 20
        
        # Interface
        self._setup_ui()
        self._setup_connections()
        self._restore_settings()
        
        # Estado inicial
        self.state_manager.change_state(AppState.INICIAL)
        self._update_window_title()
    
    def _setup_ui(self):
        """Configura interface gráfica."""
        # Propriedades da janela
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        self.setMinimumSize(1024, 600)
        self.resize(1280, 800)
        
        # Componentes principais
        self._create_menus()
        self._create_toolbars()
        self._create_central_widget()
        self._create_status_bar()
        
        # Configuração final
        self._setup_image_viewer()
    
    def _create_menus(self):
        """Cria menus da aplicação."""
        menubar = self.menuBar()
        
        # Menu Arquivo
        arquivo_menu = menubar.addMenu("&Arquivo")
        
        self.action_new_project = QAction("&Novo Projeto", self)
        self.action_new_project.setShortcut(QKeySequence.StandardKey.New)
        self.action_new_project.triggered.connect(self._new_project)
        arquivo_menu.addAction(self.action_new_project)
        
        self.action_open_image = QAction("Abrir &Imagem...", self)
        self.action_open_image.setShortcut(QKeySequence("Ctrl+I"))
        self.action_open_image.triggered.connect(self._open_image)
        arquivo_menu.addAction(self.action_open_image)
        
        self.action_open_project = QAction("&Abrir Projeto...", self)
        self.action_open_project.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open_project.triggered.connect(self._open_project)
        arquivo_menu.addAction(self.action_open_project)
        
        arquivo_menu.addSeparator()
        
        self.action_save_project = QAction("&Salvar", self)
        self.action_save_project.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save_project.setEnabled(False)
        self.action_save_project.triggered.connect(self._save_project)
        arquivo_menu.addAction(self.action_save_project)
        
        self.action_save_as = QAction("Salvar &Como...", self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.setEnabled(False)
        self.action_save_as.triggered.connect(self._save_project_as)
        arquivo_menu.addAction(self.action_save_as)
        
        arquivo_menu.addSeparator()
        
        self.action_export_image = QAction("&Exportar Imagem...", self)
        self.action_export_image.setShortcut(QKeySequence("Ctrl+E"))
        self.action_export_image.setEnabled(False)
        self.action_export_image.triggered.connect(self._export_image)
        arquivo_menu.addAction(self.action_export_image)
        
        arquivo_menu.addSeparator()
        
        self.action_exit = QAction("Sai&r", self)
        self.action_exit.setShortcut(QKeySequence("Alt+F4"))
        self.action_exit.triggered.connect(self.close)
        arquivo_menu.addAction(self.action_exit)
        
        # Menu Editar
        editar_menu = menubar.addMenu("&Editar")
        
        self.action_clear_points = QAction("&Limpar Pontos", self)
        self.action_clear_points.setShortcut(QKeySequence("Ctrl+L"))
        self.action_clear_points.setEnabled(False)
        self.action_clear_points.triggered.connect(self._clear_points)
        editar_menu.addAction(self.action_clear_points)
        
        # Menu Visualizar
        visualizar_menu = menubar.addMenu("&Visualizar")
        
        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence("Ctrl++"))
        self.action_zoom_in.triggered.connect(self._zoom_in)
        visualizar_menu.addAction(self.action_zoom_in)
        
        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        self.action_zoom_out.triggered.connect(self._zoom_out)
        visualizar_menu.addAction(self.action_zoom_out)
        
        self.action_fit_view = QAction("&Ajustar à Janela", self)
        self.action_fit_view.setShortcut(QKeySequence("Ctrl+0"))
        self.action_fit_view.triggered.connect(self._fit_in_view)
        visualizar_menu.addAction(self.action_fit_view)
        
        # Menu Ajuda
        ajuda_menu = menubar.addMenu("A&juda")
        
        self.action_about = QAction("&Sobre...", self)
        self.action_about.triggered.connect(self._show_about)
        ajuda_menu.addAction(self.action_about)
    
    def _create_toolbars(self):
        """Cria toolbars da aplicação."""
        # Toolbar principal (sempre visível com projeto)
        self.main_toolbar = QToolBar("Principal")
        self.main_toolbar.setObjectName("MainToolbar")
        self.main_toolbar.setFixedHeight(40)
        self.main_toolbar.hide()  # Oculta inicialmente
        self.addToolBar(self.main_toolbar)
        
        # Toolbar dinâmica (muda conforme estado)
        self.dynamic_toolbar = QToolBar("Dinâmica")
        self.dynamic_toolbar.setObjectName("DynamicToolbar")
        self.dynamic_toolbar.setFixedHeight(42)
        self.addToolBar(self.dynamic_toolbar)
        
        # Stack de toolbars para diferentes estados
        self.toolbar_stack = QStackedWidget()
        self.dynamic_toolbar.addWidget(self.toolbar_stack)
        
        # Criar toolbars para cada estado
        self._create_toolbar_inicial()      # 0
        self._create_toolbar_edicao()       # 1
        self._create_toolbar_marcacao()     # 2
        self._create_toolbar_medicao()      # 3
        self._create_toolbar_comparacao()   # 4
    
    def _create_toolbar_inicial(self):
        """Toolbar do estado INICIAL."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        label = QLabel("Bem-vindo ao Multímetro Inteligente! Abra uma imagem para começar.")
        label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()
        
        self.toolbar_stack.addWidget(widget)
    
    def _create_toolbar_edicao(self):
        """Toolbar do estado EDIÇÃO."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Zoom controls
        btn_zoom_in = QPushButton("🔍+")
        btn_zoom_in.setToolTip("Zoom In (Ctrl++)")
        btn_zoom_in.clicked.connect(self._zoom_in)
        layout.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton("🔍-")
        btn_zoom_out.setToolTip("Zoom Out (Ctrl+-)")
        btn_zoom_out.clicked.connect(self._zoom_out)
        layout.addWidget(btn_zoom_out)
        
        btn_fit = QPushButton("📏")
        btn_fit.setToolTip("Ajustar à Janela (Ctrl+0)")
        btn_fit.clicked.connect(self._fit_in_view)
        layout.addWidget(btn_fit)
        
        # Próximo estado
        btn_next = QPushButton("Marcar Pontos →")
        btn_next.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px; font-weight: bold;")
        btn_next.clicked.connect(lambda: self.state_manager.change_state(AppState.MARCACAO))
        layout.addWidget(btn_next)
        
        layout.addStretch()
        
        self.toolbar_stack.addWidget(widget)
    
    def _create_toolbar_marcacao(self):
        """Toolbar do estado MARCAÇÃO."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Forma do ponto
        shape_group = QButtonGroup()
        
        self.btn_circle = QPushButton("⭕ Círculo")
        self.btn_circle.setCheckable(True)
        self.btn_circle.setChecked(True)
        self.btn_circle.clicked.connect(lambda: self._set_point_shape("circle"))
        shape_group.addButton(self.btn_circle)
        layout.addWidget(self.btn_circle)
        
        self.btn_rectangle = QPushButton("⬛ Retângulo")
        self.btn_rectangle.setCheckable(True)
        self.btn_rectangle.clicked.connect(lambda: self._set_point_shape("rectangle"))
        shape_group.addButton(self.btn_rectangle)
        layout.addWidget(self.btn_rectangle)
        
        # Tamanho do ponto
        layout.addWidget(QLabel("Tamanho:"))
        self.size_spinbox = QDoubleSpinBox()
        self.size_spinbox.setRange(5, 50)
        self.size_spinbox.setValue(20)
        self.size_spinbox.setSuffix(" px")
        self.size_spinbox.valueChanged.connect(self._update_point_size)
        layout.addWidget(self.size_spinbox)
        
        # Modo edição
        self.edit_mode_btn = QCheckBox("✏️ Modo Edição")
        self.edit_mode_btn.setChecked(True)
        self.edit_mode_btn.toggled.connect(self._toggle_edit_mode)
        layout.addWidget(self.edit_mode_btn)
        
        # Limpar pontos
        btn_clear = QPushButton("🗑️ Limpar")
        btn_clear.setToolTip("Limpar todos os pontos")
        btn_clear.clicked.connect(self._clear_points)
        layout.addWidget(btn_clear)
        
        # Próximo estado
        btn_next = QPushButton("Iniciar Medição →")
        btn_next.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 16px; font-weight: bold;")
        btn_next.clicked.connect(lambda: self.state_manager.change_state(AppState.MEDICAO))
        layout.addWidget(btn_next)
        
        layout.addStretch()
        
        self.toolbar_stack.addWidget(widget)
    
    def _create_toolbar_medicao(self):
        """Toolbar do estado MEDIÇÃO."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status da medição
        self.measurement_status = QLabel("Aguardando medição...")
        self.measurement_status.setStyleSheet("color: #FF9800; font-weight: bold;")
        layout.addWidget(self.measurement_status)
        
        # Controles de medição
        btn_start_ref = QPushButton("📐 Medir Referência")
        btn_start_ref.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
        btn_start_ref.clicked.connect(lambda: self._start_measurement("reference"))
        layout.addWidget(btn_start_ref)
        
        btn_start_test = QPushButton("🔬 Medir Teste")
        btn_start_test.setStyleSheet("background-color: #FF9800; color: white; padding: 8px 16px;")
        btn_start_test.clicked.connect(lambda: self._start_measurement("test"))
        layout.addWidget(btn_start_test)
        
        # Próximo estado
        btn_next = QPushButton("Comparar Resultados →")
        btn_next.setStyleSheet("background-color: #9C27B0; color: white; padding: 8px 16px; font-weight: bold;")
        btn_next.clicked.connect(lambda: self.state_manager.change_state(AppState.COMPARACAO))
        layout.addWidget(btn_next)
        
        layout.addStretch()
        
        self.toolbar_stack.addWidget(widget)
    
    def _create_toolbar_comparacao(self):
        """Toolbar do estado COMPARAÇÃO."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Estatísticas
        self.comparison_stats = QLabel("Resultados: Analisando...")
        self.comparison_stats.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.comparison_stats)
        
        layout.addStretch()
        
        # Reiniciar
        btn_restart = QPushButton("🔄 Nova Análise")
        btn_restart.setStyleSheet("background-color: #607D8B; color: white; padding: 8px 16px;")
        btn_restart.clicked.connect(lambda: self.state_manager.change_state(AppState.EDICAO))
        layout.addWidget(btn_restart)
        
        self.toolbar_stack.addWidget(widget)
            
    def _create_central_widget(self):
        """Cria widget central com layout principal."""
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter principal
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Painel esquerdo - área da imagem
        left_panel = self._create_left_panel()
        self.main_splitter.addWidget(left_panel)
        
        # Painel direito - tabela de pontos (inicialmente oculto)
        self.right_panel = self._create_right_panel()
        self.right_panel.hide()
        self.main_splitter.addWidget(self.right_panel)
        
        # Proporção inicial (só painel esquerdo visível)
        self.main_splitter.setSizes([800, 400])
    
    def _create_left_panel(self):
        """Cria painel esquerdo com área da imagem."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack de conteúdo
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)
        
        # Tela de boas-vindas (índice 0)
        welcome_widget = self._create_welcome_widget()
        self.content_stack.addWidget(welcome_widget)
        
        # ImageViewer (índice 1) - USANDO ImageViewer REAL
        self.image_viewer = ImageViewer()
        self.content_stack.addWidget(self.image_viewer)
        
        # Info da imagem (inicialmente oculta)
        self.image_info_label = QLabel()
        self.image_info_label.setStyleSheet("background: #f0f0f0; padding: 5px; border-top: 1px solid #ccc;")
        self.image_info_label.hide()
        layout.addWidget(self.image_info_label)
        
        return panel
    
    def _create_welcome_widget(self):
        """Cria widget de boas-vindas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label principal
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                line-height: 1.5;
            }
        """)
        self._update_welcome_message()
        layout.addWidget(self.welcome_label)
        
        # Botões de ação rápida
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_open_image = QPushButton("📁 Abrir Imagem")
        btn_open_image.setStyleSheet("padding: 12px 24px; font-size: 14px;")
        btn_open_image.clicked.connect(self._open_image)
        buttons_layout.addWidget(btn_open_image)
        
        btn_open_project = QPushButton("📂 Abrir Projeto")
        btn_open_project.setStyleSheet("padding: 12px 24px; font-size: 14px;")
        btn_open_project.clicked.connect(self._open_project)
        buttons_layout.addWidget(btn_open_project)
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def _create_right_panel(self):
        """Cria painel direito com tabela de pontos."""
        panel = QFrame()
        panel.setFixedWidth(350)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        
        # Título da tabela
        self.table_title = QLabel("Pontos [0]")
        self.table_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px 0px;")
        layout.addWidget(self.table_title)
        
        # Tabela de pontos
        self.points_table = PointsTableView(self.point_manager)
        layout.addWidget(self.points_table)
        
        # Widget de tolerância (inicialmente oculto)
        self.tolerance_widget = self._create_tolerance_widget()
        self.tolerance_widget.hide()
        layout.addWidget(self.tolerance_widget)
        
        return panel
    
    def _create_tolerance_widget(self):
        """Cria widget de controle de tolerância."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 10)
        
        layout.addWidget(QLabel("Tolerância:"))
        
        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setRange(0.1, 50.0)
        self.tolerance_input.setValue(5.0)
        self.tolerance_input.setSuffix("%")
        self.tolerance_input.setToolTip("Tolerância para comparação de valores")
        self.tolerance_input.valueChanged.connect(self._apply_tolerance)
        layout.addWidget(self.tolerance_input)
        
        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(self._apply_tolerance)
        layout.addWidget(btn_apply)
        
        layout.addStretch()
        
        return widget
    
    def _create_status_bar(self):
        """Cria barra de status."""
        statusbar = self.statusBar()
        
        # Mensagem principal
        self.status_message = QLabel("Bem-vindo ao Multímetro Inteligente v1.0")
        statusbar.addWidget(self.status_message)
        
        # Info adicional
        self.status_info = QLabel("")
        statusbar.addPermanentWidget(self.status_info)
        
        # Estado atual
        self.status_state = QLabel("Estado: Inicial")
        statusbar.addPermanentWidget(self.status_state)
    
    def _setup_image_viewer(self):
        """Configura integração com ImageViewer real."""
        # Conecta ao PointManager
        self.image_viewer.set_point_manager(self.point_manager)
        
        # Conecta sinal de clique para adicionar pontos
        self.image_viewer.point_click_requested.connect(self._on_image_click)
        
        # Configurações iniciais
        self.image_viewer.set_point_shape(self.current_shape)
        self.image_viewer.set_point_size(self.current_radius)
        self.image_viewer.set_tolerance(5.0)
        self.image_viewer.set_edit_mode(False)  # Inicia desabilitado
    
    def _setup_connections(self):
        """Configura conexões de sinais."""
        # StateManager
        self.state_manager.state_changed.connect(self._update_ui_for_state)
        
        # PointManager
        self.point_manager.point_added.connect(self._on_point_added)
        self.point_manager.point_removed.connect(self._on_point_removed)
        self.point_manager.points_cleared.connect(self._on_points_cleared)
        
        # PointsTable
        if hasattr(self.points_table, 'point_selected'):
            self.points_table.point_selected.connect(self._on_point_selected)
    
    # Métodos de callback do ImageViewer
    def _on_image_click(self, x: int, y: int):
        """Callback quando usuário clica na imagem para adicionar ponto."""
        if self.state_manager.current_state == AppState.MARCACAO and self.edit_mode_btn.isChecked():
            # Adiciona ponto no PointManager
            if self.current_shape == "circle":
                point_id = self.point_manager.add_point(x, y, "circle", radius=self.current_radius)
            else:
                point_id = self.point_manager.add_point(x, y, "rectangle", 
                                                       width=self.current_width, height=self.current_height)
            
            if point_id:
                # Marca alterações não salvas
                self._mark_unsaved_changes()
                
                # Atualiza info de pontos
                self._update_points_info()
    
    # Callbacks do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        self._mark_unsaved_changes()
        self._update_points_info()
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
        self._mark_unsaved_changes()
        self._update_points_info()
    
    def _on_points_cleared(self):
        """Callback quando pontos são limpos."""
        self._mark_unsaved_changes()
        self._update_points_info()
    
    def _on_point_selected(self, point_id: int):
        """Callback quando ponto é selecionado na tabela."""
        self.image_viewer.highlight_point(point_id)
    
    # Métodos de ação de toolbar
    def _set_point_shape(self, shape: str):
        """Define forma dos pontos."""
        self.current_shape = shape
        self.image_viewer.set_point_shape(shape)
        
        # Atualiza aparência dos botões
        self.btn_circle.setChecked(shape == "circle")
        self.btn_rectangle.setChecked(shape == "rectangle")
    
    def _update_point_size(self, size: float):
        """Atualiza tamanho do ponto."""
        size_int = int(size)
        if self.current_shape == "circle":
            self.current_radius = size_int
        else:
            self.current_width = size_int
            self.current_height = size_int
        
        self.image_viewer.set_point_size(size_int)
    
    def _toggle_edit_mode(self, enabled: bool):
        """Ativa/desativa modo edição."""
        self.image_viewer.set_edit_mode(enabled)
        self.point_manager.set_edit_mode(enabled)
    
    def _clear_points(self):
        """Limpa todos os pontos."""
        if self.point_manager.get_point_count() > 0:
            reply = QMessageBox.question(
                self, "Confirmar",
                f"Remover todos os {self.point_manager.get_point_count()} pontos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.point_manager.clear_points()
    
    def _start_measurement(self, measurement_type: str):
        """Inicia sequência de medição."""
        self.measurement_status.setText(f"Iniciando medição {measurement_type}...")
        self.point_manager.start_measurement_sequence(measurement_type)
        # TODO: Implementar comunicação com hardware
    
    def _apply_tolerance(self):
        """Aplica tolerância atual."""
        tolerance = self.tolerance_input.value()
        self.points_table.set_tolerance(tolerance)
        self.image_viewer.set_tolerance(tolerance)
        self._update_comparison_stats()
    
    def _update_comparison_stats(self):
        """Atualiza estatísticas de comparação."""
        total = self.point_manager.get_point_count()
        divergent = self.point_manager.get_divergent_count(self.tolerance_input.value())
        passed = total - divergent
        
        if total > 0:
            self.comparison_stats.setText(
                f"Total: {total} | Aprovados: {passed} | Divergentes: {divergent}"
            )
            # Cor baseada no resultado
            if divergent == 0:
                self.comparison_stats.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.comparison_stats.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.comparison_stats.setText("Nenhum ponto para comparar")
    
    # Métodos de zoom e visualização
    def _zoom_in(self):
        """Zoom in na imagem."""
        self.image_viewer.zoom_in()
    
    def _zoom_out(self):
        """Zoom out na imagem."""
        self.image_viewer.zoom_out()
    
    def _fit_in_view(self):
        """Ajusta imagem na view."""
        self.image_viewer.fit_in_view()
    
    # Métodos de arquivo
    def _new_project(self):
        """Cria novo projeto."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Projeto não salvo",
                "Há alterações não salvas. Deseja continuar?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
                if not self._save_project():
                    return
        
        # Limpa estado atual
        self.project = None
        self.current_file_path = None
        self.has_unsaved_changes = False
        
        # Reset componentes
        self.image_viewer.clear()
        self.point_manager.clear_points()
        
        # Volta ao estado inicial
        self.state_manager.change_state(AppState.INICIAL)
        self._update_window_title()
    
    def _open_image(self):
        """Abre dialog para selecionar imagem."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem",
            "", "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            self._load_image(file_path)
    
    def _load_image(self, file_path: str):
        """Carrega imagem selecionada."""
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self._show_error("Não foi possível carregar a imagem.\nVerifique se o arquivo é uma imagem válida.")
                return
            
            # Cria novo projeto se não existir
            if not self.project:
                self.project = BoardProject(
                    name="Novo Projeto",
                    board_model="Modelo Desconhecido",
                    is_fully_functional=True
                )
            
            # Carrega imagem no viewer
            self.image_viewer.set_image(pixmap)
            
            # Atualiza interface
            self.content_stack.setCurrentIndex(1)  # Mostra ImageViewer
            self.state_manager.change_state(AppState.EDICAO)
            
            # Mostra informações da imagem
            self.image_info_label.setText(f"Imagem: {pixmap.width()}x{pixmap.height()}px - {file_path}")
            self.image_info_label.show()
            
            # Atualiza ações
            self._update_actions()
            self._update_window_title()
            
            # Status
            self.status_message.setText("Imagem carregada com sucesso. Você pode começar a editar.")
            
        except Exception as e:
            self._show_error(f"Erro ao carregar imagem:\n{str(e)}")
    
    def _open_project(self):
        """Abre dialog para selecionar projeto."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto",
            "", "Projetos MIP (*.mip);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            self._load_project(file_path)
    
    def _load_project(self, file_path: str):
        """Carrega projeto selecionado."""
        try:
            project_data = ProjectPersistence.load(file_path)
            if not project_data:
                self._show_error("Não foi possível carregar o projeto.\nVerifique se o arquivo é válido.")
                return
            
            # TODO: Implementar carregamento completo do projeto
            self.current_file_path = file_path
            self.has_unsaved_changes = False
            
            self.status_message.setText(f"Projeto carregado: {file_path}")
            self._update_window_title()
            
        except Exception as e:
            self._show_error(f"Erro ao carregar projeto:\n{str(e)}")
    
    def _save_project(self) -> bool:
        """Salva projeto atual."""
        if not self.project:
            return False
        
        if self.current_file_path:
            return self._save_project_to_file(self.current_file_path)
        else:
            return self._save_project_as()
    
    def _save_project_as(self) -> bool:
        """Salva projeto com novo nome."""
        if not self.project:
            return False
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeto Como",
            f"{self.project.name}.mip",
            "Projetos MIP (*.mip);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            return self._save_project_to_file(file_path)
        return False
    
    def _save_project_to_file(self, file_path: str) -> bool:
        """Salva projeto em arquivo específico."""
        try:
            # Monta dados do projeto
            project_data = {
                "project": self.project.__dict__ if self.project else {},
                "points": [point.__dict__ for point in self.point_manager.get_all_points()],
                "image_data": self.image_viewer.get_image_data(),
                "settings": {
                    "tolerance": self.tolerance_input.value(),
                    "current_shape": self.current_shape,
                    "current_radius": self.current_radius
                }
            }
            
            if ProjectPersistence.save(project_data, file_path):
                self.current_file_path = file_path
                self.has_unsaved_changes = False
                self.status_message.setText(f"Projeto salvo: {file_path}")
                self._update_window_title()
                return True
            else:
                self._show_error("Erro ao salvar projeto.")
                return False
                
        except Exception as e:
            self._show_error(f"Erro ao salvar projeto:\n{str(e)}")
            return False
    
    def _export_image(self):
        """Exporta imagem com pontos."""
        if not self.image_viewer.image_pixmap:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Imagem",
            "imagem_com_pontos.png",
            "PNG (*.png);;JPEG (*.jpg);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            if self.image_viewer.export_image_with_points(file_path):
                self.status_message.setText(f"Imagem exportada: {file_path}")
            else:
                self._show_error("Erro ao exportar imagem.")
    
    # Métodos de estado
    @pyqtSlot(AppState)
    def _update_ui_for_state(self, state: AppState):
        """Atualiza interface para novo estado."""
        # Status bar
        self.status_state.setText(f"Estado: {state.value.title()}")
        
        # Toolbar dinâmica
        self.toolbar_stack.setCurrentIndex(state.to_index())
        
        # Painel direito (tabela de pontos)
        show_right_panel = state in [AppState.MARCACAO, AppState.MEDICAO, AppState.COMPARACAO]
        if show_right_panel:
            self.right_panel.show()
        else:
            self.right_panel.hide()
        
        # Controle de tolerância - VERSÃO CORRIGIDA
        if state == AppState.COMPARACAO:
            # Garantir que o painel pai está visível primeiro
            if hasattr(self, 'right_panel') and not self.right_panel.isVisible():
                self.right_panel.show()
            
            # Mostrar o widget de tolerância
            self.tolerance_widget.setVisible(True)
            
            # Forçar atualização do layout
            self.tolerance_widget.updateGeometry()
            if self.tolerance_widget.parent():
                self.tolerance_widget.parent().updateGeometry()
        else:
            self.tolerance_widget.setVisible(False)
        
        # Atualiza ações baseadas no estado
        self._update_actions()
        
        # Configurações específicas por estado
        if state == AppState.MARCACAO:
            self.image_viewer.set_edit_mode(True)
            if hasattr(self, 'edit_mode_btn'):
                self.edit_mode_btn.setChecked(True)
        else:
            self.image_viewer.set_edit_mode(False)
    
    def _update_actions(self):
        """Atualiza estado das ações baseado no contexto."""
        has_project = self.project is not None
        has_image = self.image_viewer.image_pixmap is not None
        has_points = self.point_manager.get_point_count() > 0
        
        # Ações de arquivo
        self.action_save_project.setEnabled(has_project)
        self.action_save_as.setEnabled(has_project)
        self.action_export_image.setEnabled(has_image)
        self.action_clear_points.setEnabled(has_points)
    
    def _update_points_info(self):
        """Atualiza informações dos pontos."""
        total = self.point_manager.get_point_count()
        measured = self.point_manager.get_measured_count()
        
        # Atualiza título da tabela
        self.table_title.setText(f"Pontos [{total}]")
        
        # Atualiza status bar
        if total > 0:
            self.status_info.setText(f"Pontos: {total} | Medidos: {measured}")
        else:
            self.status_info.setText("")
    
    def _update_window_title(self):
        """Atualiza título da janela."""
        base_title = "Multímetro Inteligente - v1.0"
        
        if self.project:
            title = f"{base_title} - {self.project.name}"
            if self.has_unsaved_changes:
                title += " *"
        else:
            title = base_title
        
        self.setWindowTitle(title)
    
    def _mark_unsaved_changes(self):
        """Marca que há alterações não salvas."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_window_title()
    
    def _update_welcome_message(self):
        """Atualiza mensagem de boas-vindas."""
        self.welcome_label.setText("""
            <h2>🔍 Multímetro Inteligente v1.0</h2>
            <p>Sistema de mapeamento e comparação de placas eletrônicas</p>
            <br>
            <p><strong>Para começar:</strong></p>
            <p>• <strong>Abrir Imagem</strong> - Carregue uma foto da placa eletrônica</p>
            <p>• <strong>Abrir Projeto</strong> - Continue trabalhando em um projeto salvo (.mip)</p>
        """)
    
    # Métodos utilitários
    def _show_error(self, message: str):
        """Mostra dialog de erro."""
        QMessageBox.critical(self, "Erro", message)
    
    def _show_about(self):
        """Mostra dialog sobre."""
        QMessageBox.about(self, "Sobre o Multímetro Inteligente", 
            """<h3>Multímetro Inteligente v1.0</h3>
            <p>Sistema desktop para mapeamento e comparação de placas eletrônicas.</p>
            <p><b>Funcionalidades:</b></p>
            <ul>
            <li>Carregamento de imagens de placas</li>
            <li>Marcação visual de pontos de medição</li>
            <li>Medição automática via multímetro</li>
            <li>Comparação com tolerâncias configuráveis</li>
            <li>Salvamento de projetos (.mip)</li>
            </ul>
            <p><b>Desenvolvido para técnicos em eletrônica</b></p>
            """)
    
    # Eventos
    def keyPressEvent(self, event: QKeyEvent):
        """Trata eventos de teclado."""
        # Atalhos específicos por estado
        if (self.state_manager.current_state == AppState.MARCACAO and 
            hasattr(self, 'size_spinbox')):
            if event.key() == Qt.Key.Key_W:
                # Aumenta tamanho do ponto
                current = self.size_spinbox.value()
                self.size_spinbox.setValue(min(50, current + 1))
            elif event.key() == Qt.Key.Key_S:
                # Diminui tamanho do ponto
                current = self.size_spinbox.value()
                self.size_spinbox.setValue(max(5, current - 1))
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event: QCloseEvent):
        """Trata evento de fechamento da janela."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Multímetro Inteligente",
                "Há alterações não salvas. Deseja salvar antes de sair?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.StandardButton.Save:
                if not self._save_project():
                    event.ignore()
                    return
        
        # Salva configurações
        self._save_settings()
        event.accept()
    
    # Configurações
    def _save_settings(self):
        """Salva configurações da aplicação."""
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("splitter/sizes", self.main_splitter.sizes())
        self.settings.setValue("tolerance", self.tolerance_input.value())
        self.settings.setValue("shape", self.current_shape)
        self.settings.setValue("radius", self.current_radius)
    
    def _restore_settings(self):
        """Restaura configurações da aplicação."""
        # Geometria da janela
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Estado da janela
        state = self.settings.value("window/state")
        if state:
            self.restoreState(state)
        
        # Splitter
        sizes = self.settings.value("splitter/sizes")
        if sizes:
            self.main_splitter.setSizes([int(s) for s in sizes])
        
        # Tolerância
        tolerance = self.settings.value("tolerance", 5.0, type=float)
        self.tolerance_input.setValue(tolerance)
        
        # Forma e tamanho
        shape = self.settings.value("shape", "circle", type=str)
        if shape == "rectangle":
            self._set_point_shape("rectangle")
        
        radius = self.settings.value("radius", 20, type=int)
        if hasattr(self, 'size_spinbox'):
            self.size_spinbox.setValue(radius)