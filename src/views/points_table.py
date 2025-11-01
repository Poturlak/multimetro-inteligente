# -*- coding: utf-8 -*-
"""
PointsTableView - Tabela para visualização e edição de pontos de medição.
VERSÃO CORRIGIDA - Remove sinal point_measured que não existe
"""

from typing import Optional, List
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QBrush

from src.models.point import Point
from src.controllers.point_manager import PointManager


class PointsTableView(QTableWidget):
    """
    Tabela personalizada para exibir e gerenciar pontos de medição.
    
    Funcionalidades:
    - Lista todos os pontos com ID, posição, formato e valores
    - Destaque de pontos selecionados
    - Cores baseadas em tolerância
    - Integração com PointManager
    """
    
    # Sinais
    point_selected = pyqtSignal(int)  # point_id selecionado
    
    def __init__(self, point_manager: PointManager):
        super().__init__()
        
        self.point_manager = point_manager
        self.tolerance = 5.0
        
        # Configuração da tabela
        self._setup_table()
        
        # Conecta sinais do PointManager
        self._setup_connections()
        
        # Atualiza dados iniciais
        self._refresh_data()
    
    def _setup_table(self):
        """Configura propriedades da tabela."""
        # Colunas
        self.setColumnCount(6)
        headers = ["ID", "X", "Y", "Forma", "Ref", "Teste"]
        self.setHorizontalHeaderLabels(headers)
        
        # Propriedades
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Redimensionamento das colunas
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # X
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Y
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Forma
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Ref
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Teste
        
        # Altura das linhas
        self.verticalHeader().setDefaultSectionSize(25)
        self.verticalHeader().hide()
    
    def _setup_connections(self):
        """Conecta sinais do PointManager."""
        if self.point_manager:
            self.point_manager.point_added.connect(self._on_point_added)
            self.point_manager.point_removed.connect(self._on_point_removed)
            self.point_manager.points_cleared.connect(self._on_points_cleared)
            
            # ✅ CORREÇÃO: Remove conexão com sinal que não existe
            # self.point_manager.point_measured.connect(self._on_point_measured)
        
        # Seleção na tabela
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def set_tolerance(self, tolerance: float):
        """Define tolerância para análise de divergências."""
        self.tolerance = tolerance
        self._refresh_colors()
    
    def _refresh_data(self):
        """Atualiza dados da tabela."""
        if not self.point_manager:
            return
        
        points = self.point_manager.get_all_points()
        self.setRowCount(len(points))
        
        for row, point in enumerate(points):
            self._update_row(row, point)
        
        self._refresh_colors()
    
    def _update_row(self, row: int, point: Point):
        """Atualiza uma linha da tabela."""
        # ID
        id_item = QTableWidgetItem(str(point.id))
        id_item.setData(Qt.ItemDataRole.UserRole, point.id)
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 0, id_item)
        
        # Posição X
        x_item = QTableWidgetItem(str(point.x))
        x_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 1, x_item)
        
        # Posição Y  
        y_item = QTableWidgetItem(str(point.y))
        y_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 2, y_item)
        
        # Forma
        shape_text = "⭕" if point.shape == "circle" else "⬛"
        if hasattr(point, 'radius') and point.radius:
            size = str(point.radius)
        elif hasattr(point, 'width') and hasattr(point, 'height') and point.width and point.height:
            size = f"{point.width}x{point.height}"
        else:
            size = "20"  # default
        shape_item = QTableWidgetItem(f"{shape_text} {size}")
        shape_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 3, shape_item)
        
        # Valor de referência
        ref_text = "---"
        if hasattr(point, 'reference_value') and point.reference_value is not None:
            ref_text = f"{point.reference_value:.2f}"
        ref_item = QTableWidgetItem(ref_text)
        ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 4, ref_item)
        
        # Valor de teste
        test_text = "---"
        if hasattr(point, 'test_value') and point.test_value is not None:
            test_text = f"{point.test_value:.2f}"
        test_item = QTableWidgetItem(test_text)
        test_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 5, test_item)
    
    def _refresh_colors(self):
        """Atualiza cores das linhas baseado na tolerância."""
        for row in range(self.rowCount()):
            point_id_item = self.item(row, 0)
            if not point_id_item:
                continue
            
            point_id = point_id_item.data(Qt.ItemDataRole.UserRole)
            point = self.point_manager.get_point(point_id)
            
            # Determina cor baseada no ponto
            if point:
                # Verifica se tem método is_divergent
                if hasattr(point, 'is_divergent') and point.is_divergent(self.tolerance):
                    color = QColor(255, 200, 200)  # Vermelho claro para divergente
                elif (hasattr(point, 'reference_value') and hasattr(point, 'test_value') and 
                      point.reference_value is not None and point.test_value is not None):
                    color = QColor(200, 255, 200)  # Verde claro para medido e OK
                else:
                    color = QColor(255, 255, 255)  # Branco para padrão
            else:
                color = QColor(255, 255, 255)  # Branco padrão
            
            # Aplica cor a todas as células da linha
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(QBrush(color))
    
    def _on_selection_changed(self):
        """Callback quando seleção muda."""
        selected_items = self.selectedItems()
        if selected_items:
            # Pega o ID da primeira célula da linha selecionada
            row = selected_items[0].row()
            id_item = self.item(row, 0)
            if id_item:
                point_id = id_item.data(Qt.ItemDataRole.UserRole)
                self.point_selected.emit(point_id)
    
    def highlight_point(self, point_id: int):
        """Destaca um ponto específico na tabela."""
        for row in range(self.rowCount()):
            id_item = self.item(row, 0)
            if id_item and id_item.data(Qt.ItemDataRole.UserRole) == point_id:
                self.selectRow(row)
                self.scrollToItem(id_item)
                break
    
    # Slots dos sinais do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        self._refresh_data()
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
        # Remove linha da tabela
        for row in range(self.rowCount()):
            id_item = self.item(row, 0)
            if id_item and id_item.data(Qt.ItemDataRole.UserRole) == point_id:
                self.removeRow(row)
                break
        
        self._refresh_colors()
    
    def _on_points_cleared(self):
        """Callback quando todos os pontos são removidos."""
        self.setRowCount(0)
    
    # ✅ MÉTODO OPCIONAL - pode ser chamado manualmente quando medição for implementada
    def refresh_point_data(self, point_id: int):
        """Atualiza dados de um ponto específico na tabela."""
        for row in range(self.rowCount()):
            id_item = self.item(row, 0)
            if id_item and id_item.data(Qt.ItemDataRole.UserRole) == point_id:
                point = self.point_manager.get_point(point_id)
                if point:
                    self._update_row(row, point)
                break
        
        # Atualiza cores
        QTimer.singleShot(100, self._refresh_colors)