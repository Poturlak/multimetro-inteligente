# -*- coding: utf-8 -*-
"""
ImageViewer - Versão Atualizada com Transformações de Imagem
- Rotação 90°
- Espelhamento Horizontal/Vertical
- Integração com PointManager
- Export de imagem com pontos
"""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QColor, QBrush, QWheelEvent, QPaintEvent
import base64
from io import BytesIO

from src.controllers.point_manager import PointManager
from src.models.point import Point


class ImageViewer(QGraphicsView):
    """
    Visualizador de imagens com funcionalidades de transformação.
    
    FUNCIONALIDADES IMPLEMENTADAS:
    - Zoom/Pan
    - Rotação 90°
    - Espelhamento H/V
    - Renderização de pontos
    - Export com pontos
    """
    
    # Sinais
    point_click_requested = pyqtSignal(int, int)  # x, y na imagem
    
    def __init__(self):
        super().__init__()
        
        # Configuração inicial
        self._setup_viewer()
        
        # Estado da imagem
        self.image_pixmap: Optional[QPixmap] = None
        self.original_pixmap: Optional[QPixmap] = None  # ✅ NOVO: Backup do original
        
        # Scene e items
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        
        # ✅ NOVO: Sistema de transformações
        self.current_transform = QTransform()  # Transformação acumulada
        self.transform_history: List[QTransform] = []  # Para desfazer/refazer
        
        # Integração com pontos
        self.point_manager: Optional[PointManager] = None
        self.current_shape = "circle"
        self.current_size = 20
        self.tolerance = 5.0
        self.edit_mode = False
        
        # Estado de interação
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        print("✅ ImageViewer inicializado com transformações")
    
    def _setup_viewer(self):
        """Configuração inicial do viewer."""
        # Configurações básicas
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Fundo cinza claro
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        
        # Zoom limits
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.zoom_factor = 1.15
    
    # ========== ✅ NOVOS MÉTODOS DE TRANSFORMAÇÃO ==========
    
    def rotate_image(self, angle: float) -> bool:
        """
        Rotaciona imagem no ângulo especificado.
        
        Args:
            angle: Ângulo em graus (positivo = horário)
            
        Returns:
            True se rotação foi bem-sucedida
        """
        if not self.image_pixmap:
            print("❌ Nenhuma imagem carregada para rotacionar")
            return False
        
        try:
            # ✅ TRANSFORMAÇÃO: Rotaciona o pixmap atual
            transform = QTransform().rotate(angle)
            rotated_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # Salva transformação no histórico
            self.transform_history.append(self.current_transform)
            self.current_transform = self.current_transform * transform
            
            # Atualiza imagem
            self._update_pixmap(rotated_pixmap)
            
            print(f"✅ Imagem rotacionada {angle}°")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rotacionar imagem: {e}")
            return False
    
    def flip_image(self, horizontal: bool) -> bool:
        """
        Espelha imagem horizontal ou verticalmente.
        
        Args:
            horizontal: True para espelhar horizontalmente, False para verticalmente
            
        Returns:
            True se espelhamento foi bem-sucedido
        """
        if not self.image_pixmap:
            print("❌ Nenhuma imagem carregada para espelhar")
            return False
        
        try:
            # ✅ TRANSFORMAÇÃO: Espelha o pixmap atual
            if horizontal:
                transform = QTransform().scale(-1, 1)  # Inverte X
                direction = "horizontalmente"
            else:
                transform = QTransform().scale(1, -1)  # Inverte Y
                direction = "verticalmente"
            
            flipped_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # Salva transformação no histórico
            self.transform_history.append(self.current_transform)
            self.current_transform = self.current_transform * transform
            
            # Atualiza imagem
            self._update_pixmap(flipped_pixmap)
            
            print(f"✅ Imagem espelhada {direction}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao espelhar imagem: {e}")
            return False
    
    def reset_transformations(self) -> bool:
        """
        Reseta todas as transformações para a imagem original.
        
        Returns:
            True se reset foi bem-sucedido
        """
        if not self.original_pixmap:
            print("❌ Imagem original não disponível")
            return False
        
        try:
            # Salva estado atual no histórico
            self.transform_history.append(self.current_transform)
            
            # Reseta para original
            self.current_transform = QTransform()
            self._update_pixmap(self.original_pixmap.copy())
            
            print("✅ Transformações resetadas")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao resetar transformações: {e}")
            return False
    
    def _update_pixmap(self, new_pixmap: QPixmap):
        """
        Atualiza pixmap exibido.
        
        Args:
            new_pixmap: Novo pixmap para exibir
        """
        self.image_pixmap = new_pixmap
        
        if self.pixmap_item:
            self.pixmap_item.setPixmap(new_pixmap)
        else:
            self.pixmap_item = self.scene.addPixmap(new_pixmap)
        
        # Centraliza imagem na scene
        self._center_image()
        
        # Redesenha pontos se houver
        if self.point_manager:
            self._render_points()
    
    # ========== MÉTODOS ORIGINAIS (mantidos) ==========
    
    def set_image(self, pixmap: QPixmap):
        """Carrega nova imagem."""
        try:
            # ✅ NOVO: Salva cópia do original
            self.original_pixmap = pixmap.copy()
            self.image_pixmap = pixmap.copy()
            
            # Reseta transformações
            self.current_transform = QTransform()
            self.transform_history.clear()
            
            # Limpa scene atual
            self.scene.clear()
            self.pixmap_item = None
            
            # Adiciona novo pixmap
            self.pixmap_item = self.scene.addPixmap(self.image_pixmap)
            
            # Ajusta view
            self._center_image()
            self.fit_in_view()
            
            print(f"✅ Imagem carregada: {pixmap.width()}x{pixmap.height()}px")
            
        except Exception as e:
            print(f"❌ Erro ao carregar imagem: {e}")
    
    def clear(self):
        """Limpa imagem atual."""
        self.scene.clear()
        self.image_pixmap = None
        self.original_pixmap = None
        self.pixmap_item = None
        self.current_transform = QTransform()
        self.transform_history.clear()
        print("✅ Imagem limpa")
    
    def _center_image(self):
        """Centraliza imagem na scene."""
        if self.image_pixmap:
            rect = QRectF(self.image_pixmap.rect())
            self.scene.setSceneRect(rect)
            self.centerOn(rect.center())
    
    # Zoom e navegação
    def wheelEvent(self, event: QWheelEvent):
        """Controla zoom com scroll do mouse."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """Aumenta zoom."""
        current_scale = self.transform().m11()
        if current_scale < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
    
    def zoom_out(self):
        """Diminui zoom."""
        current_scale = self.transform().m11()
        if current_scale > self.min_zoom:
            self.scale(1/self.zoom_factor, 1/self.zoom_factor)
    
    def fit_in_view(self):
        """Ajusta imagem para caber na view."""
        if self.image_pixmap:
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    # Eventos do mouse
    def mousePressEvent(self, event):
        """Trata clique do mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Verifica se deve adicionar ponto
            if self.edit_mode and self.state_manager and self.state_manager.current_state.value == "marcacao":
                scene_pos = self.mapToScene(event.pos())
                if self.pixmap_item and self.pixmap_item.boundingRect().contains(scene_pos):
                    # Coordenadas na imagem
                    image_pos = scene_pos - self.pixmap_item.boundingRect().topLeft()
                    x, y = int(image_pos.x()), int(image_pos.y())
                    
                    # Emite sinal para adicionar ponto
                    self.point_click_requested.emit(x, y)
                    return
            
            # Pan mode
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Trata movimento do mouse."""
        if self.is_panning and event.buttons() == Qt.MouseButton.LeftButton:
            # Pan da imagem
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            # Move scrollbars
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Trata soltar do mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Cursor ao entrar."""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Cursor ao sair."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    # ========== INTEGRAÇÃO COM PONTOS ==========
    
    def set_point_manager(self, point_manager: PointManager):
        """Define gerenciador de pontos."""
        self.point_manager = point_manager
        if point_manager:
            # Conecta sinais
            point_manager.point_added.connect(self._on_point_added)
            point_manager.point_removed.connect(self._on_point_removed)
            point_manager.points_cleared.connect(self._on_points_cleared)
            print("✅ PointManager conectado ao ImageViewer")
    
    def set_point_shape(self, shape: str):
        """Define forma dos pontos."""
        self.current_shape = shape
    
    def set_point_size(self, size: int):
        """Define tamanho dos pontos."""
        self.current_size = size
    
    def set_tolerance(self, tolerance: float):
        """Define tolerância."""
        self.tolerance = tolerance
        self._render_points()  # Re-renderiza com novas cores
    
    def set_edit_mode(self, enabled: bool):
        """Define modo de edição."""
        self.edit_mode = enabled
        
        # Adiciona referência ao state_manager quando necessário
        if not hasattr(self, 'state_manager'):
            # Hack temporário - em implementação futura, passar via construtor
            from src.controllers.state_manager import AppState
            self.state_manager = type('MockStateManager', (), {'current_state': AppState.MARCACAO})()
    
    def _render_points(self):
        """Renderiza pontos na imagem."""
        if not self.point_manager or not self.pixmap_item:
            return
        
        # Remove pontos existentes da scene
        for item in self.scene.items():
            if hasattr(item, 'is_point_item'):
                self.scene.removeItem(item)
        
        # Adiciona todos os pontos
        for point in self.point_manager.get_all_points():
            self._add_point_to_scene(point)
    
    def _add_point_to_scene(self, point: Point):
        """Adiciona ponto individual à scene."""
        # Determina cor baseada no status
        if point.is_measured():
            if point.is_divergent(self.tolerance):
                color = QColor(255, 0, 0, 128)  # Vermelho transparente
            else:
                color = QColor(0, 255, 0, 128)  # Verde transparente
        else:
            color = QColor(0, 0, 255, 128)  # Azul transparente
        
        # Posição na scene (relativa ao pixmap)
        if self.pixmap_item:
            scene_x = self.pixmap_item.boundingRect().x() + point.x
            scene_y = self.pixmap_item.boundingRect().y() + point.y
            
            # Cria item gráfico baseado na forma
            if point.shape == "circle":
                from PyQt6.QtWidgets import QGraphicsEllipseItem
                radius = point.radius or 20
                item = QGraphicsEllipseItem(scene_x - radius, scene_y - radius, radius * 2, radius * 2)
            else:
                from PyQt6.QtWidgets import QGraphicsRectItem
                width = point.width or 20
                height = point.height or 20
                item = QGraphicsRectItem(scene_x - width/2, scene_y - height/2, width, height)
            
            # Configura aparência
            item.setBrush(QBrush(color))
            item.setPen(Qt.GlobalColor.black)
            item.is_point_item = True  # Marca para identificação
            item.point_id = point.id
            
            self.scene.addItem(item)
    
    def highlight_point(self, point_id: int):
        """Destaca ponto específico."""
        # TODO: Implementar highlight visual
        print(f"✅ Destacando ponto #{point_id}")
    
    # Callbacks do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        self._add_point_to_scene(point)
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
        # Remove da scene
        for item in self.scene.items():
            if hasattr(item, 'point_id') and item.point_id == point_id:
                self.scene.removeItem(item)
                break
    
    def _on_points_cleared(self):
        """Callback quando pontos são limpos."""
        self._render_points()
    
    # ========== ✅ NOVO: EXPORT COM PONTOS ==========
    
    def export_image_with_points(self, file_path: str) -> bool:
        """
        Exporta imagem atual com pontos renderizados.
        
        Args:
            file_path: Caminho do arquivo de destino
            
        Returns:
            True se export foi bem-sucedido
        """
        if not self.image_pixmap:
            print("❌ Nenhuma imagem para exportar")
            return False
        
        try:
            # Cria cópia da imagem atual
            export_pixmap = self.image_pixmap.copy()
            
            # Renderiza pontos na imagem
            if self.point_manager:
                painter = QPainter(export_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                for point in self.point_manager.get_all_points():
                    # Determina cor
                    if point.is_measured():
                        if point.is_divergent(self.tolerance):
                            color = QColor(255, 0, 0, 180)  # Vermelho
                        else:
                            color = QColor(0, 255, 0, 180)  # Verde
                    else:
                        color = QColor(0, 0, 255, 180)  # Azul
                    
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.GlobalColor.black)
                    
                    # Desenha forma
                    if point.shape == "circle":
                        radius = point.radius or 20
                        painter.drawEllipse(point.x - radius, point.y - radius, radius * 2, radius * 2)
                    else:
                        width = point.width or 20
                        height = point.height or 20
                        painter.drawRect(point.x - width//2, point.y - height//2, width, height)
                
                painter.end()
            
            # Salva arquivo
            success = export_pixmap.save(file_path)
            
            if success:
                print(f"✅ Imagem exportada: {file_path}")
            else:
                print(f"❌ Falha ao salvar: {file_path}")
            
            return success
            
        except Exception as e:
            print(f"❌ Erro ao exportar imagem: {e}")
            return False
    
    def get_image_data(self) -> Optional[str]:
        """
        Obtém dados da imagem atual como string base64.
        
        Returns:
            String base64 da imagem ou None se erro
        """
        if not self.image_pixmap:
            return None
        
        try:
            # Converte pixmap para bytes
            byte_array = BytesIO()
            self.image_pixmap.save(byte_array, "PNG")
            
            # Codifica em base64
            image_data = base64.b64encode(byte_array.getvalue()).decode()
            
            return image_data
            
        except Exception as e:
            print(f"❌ Erro ao obter dados da imagem: {e}")
            return None