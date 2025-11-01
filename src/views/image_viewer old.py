# -*- coding: utf-8 -*-
"""
ImageViewer - QGraphicsView customizado para visualização de imagem com pontos de medição.

Funcionalidades:
- Carregamento e exibição de imagem
- Zoom e pan
- Overlay de pontos de medição (círculos/retângulos)
- Preview de ponto ao mover mouse
- Modo de edição de pontos
- Animação de piscada para medição ativa
"""

from typing import Optional, Dict, Tuple, List
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
    QGraphicsItem, QApplication
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QWheelEvent, QMouseEvent, QPainter, QPen, 
    QBrush, QColor, QFont, QCursor, QTransform
)
from src.models.point import Point
from src.controllers.point_manager import PointManager


class PointGraphicsItem(QGraphicsItem):
    """Item gráfico para representar um ponto de medição."""
    
    def __init__(self, point: Point, tolerance: float = 5.0):
        super().__init__()
        self.point = point
        self.tolerance = tolerance
        self.is_blinking = False
        self.blink_opacity = 1.0
        self.blink_timer: Optional[QTimer] = None
        
        # Configurações
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
    def boundingRect(self) -> QRectF:
        """Define área de desenho do item."""
        margin = 4  # Margem extra para borda
        
        if self.point.shape == "circle":
            r = self.point.radius or 20
            return QRectF(-r - margin, -r - margin, 2*r + 2*margin, 2*r + 2*margin)
        else:  # rectangle
            w = self.point.width or 20
            h = self.point.height or 20
            return QRectF(-w/2 - margin, -h/2 - margin, w + 2*margin, h + 2*margin)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Renderiza o ponto."""
        # Determina cor baseada no status
        if self.point.is_divergent(self.tolerance):
            color = QColor(255, 105, 180, 150)  # Rosa para divergente
        else:
            color = QColor(255, 0, 0, 120)  # Vermelho normal
        
        # Aplica opacidade se piscando
        if self.is_blinking:
            color.setAlpha(int(color.alpha() * self.blink_opacity))
        
        # Configurações do painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color.darker(), 2))
        painter.setBrush(QBrush(color))
        
        # Desenha forma
        if self.point.shape == "circle":
            r = self.point.radius or 20
            painter.drawEllipse(QPointF(0, 0), r, r)
        else:  # rectangle
            w = self.point.width or 20
            h = self.point.height or 20
            painter.drawRect(QRectF(-w/2, -h/2, w, h))
        
        # Desenha ID
        self._draw_id(painter)
    
    def _draw_id(self, painter: QPainter):
        """Desenha o ID do ponto."""
        font = painter.font()
        font.setBold(True)
        
        # Tamanho da fonte baseado no tamanho do ponto
        if self.point.shape == "circle":
            font_size = max(8, int((self.point.radius or 20) * 0.5))
        else:
            w = self.point.width or 20
            h = self.point.height or 20
            font_size = max(8, int(min(w, h) * 0.4))
        
        font.setPointSize(font_size)
        painter.setFont(font)
        
        # Texto branco com contorno
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, str(self.point.id))
    
    def start_blinking(self):
        """Inicia animação de piscada."""
        self.is_blinking = True
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._animate_blink)
        self.blink_timer.start(50)  # 20fps
    
    def stop_blinking(self):
        """Para animação de piscada."""
        self.is_blinking = False
        self.blink_opacity = 1.0
        if self.blink_timer:
            self.blink_timer.stop()
        self.update()
    
    def _animate_blink(self):
        """Anima a piscada."""
        # Oscila opacidade entre 0.3 e 1.0
        self.blink_opacity -= 0.1
        if self.blink_opacity <= 0.3:
            self.blink_opacity = 1.0
        self.update()
    
    def set_tolerance(self, tolerance: float):
        """Atualiza tolerância e força redesenho."""
        self.tolerance = tolerance
        self.update()


class PreviewPointItem(QGraphicsItem):
    """Item gráfico para preview do ponto ao mover mouse."""
    
    def __init__(self, shape: str, radius: int = 20, width: int = 20, height: int = 20):
        super().__init__()
        self.shape = shape
        self.radius = radius
        self.width = width
        self.height = height
        self.setZValue(10)  # Sempre no topo
    
    def boundingRect(self) -> QRectF:
        """Define área de desenho."""
        margin = 2
        if self.shape == "circle":
            return QRectF(-self.radius - margin, -self.radius - margin, 
                         2*self.radius + 2*margin, 2*self.radius + 2*margin)
        else:
            return QRectF(-self.width/2 - margin, -self.height/2 - margin, 
                         self.width + 2*margin, self.height + 2*margin)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Renderiza o preview."""
        # Cor transparente para preview
        color = QColor(255, 0, 0, 80)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(color))
        
        if self.shape == "circle":
            painter.drawEllipse(QPointF(0, 0), self.radius, self.radius)
        else:
            painter.drawRect(QRectF(-self.width/2, -self.height/2, self.width, self.height))
    
    def update_size(self, radius: int = None, width: int = None, height: int = None):
        """Atualiza tamanho do preview."""
        if radius is not None:
            self.radius = radius
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        self.update()


class ImageViewer(QGraphicsView):
    """
    Visualizador de imagem customizado com suporte a:
    - Zoom e pan
    - Overlay de pontos de medição
    - Preview de ponto
    - Modo de edição
    """
    
    # Sinais
    point_click_requested = pyqtSignal(int, int)  # x, y para adicionar ponto
    point_moved = pyqtSignal(int, int, int)  # point_id, new_x, new_y
    
    def __init__(self):
        super().__init__()
        
        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Estado
        self.image_item: Optional[QGraphicsPixmapItem] = None
        self.image_pixmap: Optional[QPixmap] = None
        self.point_manager: Optional[PointManager] = None
        
        # Pontos visuais
        self.point_items: Dict[int, PointGraphicsItem] = {}
        self.preview_item: Optional[PreviewPointItem] = None
        
        # Configurações de ponto
        self.current_shape = "circle"
        self.current_radius = 20
        self.current_width = 20
        self.current_height = 20
        self.tolerance = 5.0
        
        # Estado de interação
        self.zoom_factor = 1.0
        self.is_panning = False
        self.pan_start = QPointF()
        self.edit_mode = False
        
        # Configurações da view
        self._setup_view()
    
    def _setup_view(self):
        """Configura propriedades da view."""
        # Renderização
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Interação
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Aparência
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))  # Cinza claro
        
        # Mouse tracking para preview
        self.setMouseTracking(True)
    
    def set_image(self, pixmap: QPixmap):
        """Carrega imagem na view."""
        self.image_pixmap = pixmap
        
        # Remove imagem anterior
        if self.image_item:
            self.scene.removeItem(self.image_item)
        
        # Adiciona nova imagem
        self.image_item = self.scene.addPixmap(pixmap)
        self.image_item.setZValue(0)  # Camada de fundo
        
        # Ajusta cena ao tamanho da imagem
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        # Fit na view
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_factor = 1.0
    
    def set_point_manager(self, point_manager: PointManager):
        """Define o gerenciador de pontos."""
        self.point_manager = point_manager
        
        # Conecta sinais do point manager
        if point_manager:
            point_manager.point_added.connect(self._on_point_added)
            point_manager.point_removed.connect(self._on_point_removed)
            point_manager.points_cleared.connect(self._on_points_cleared)
    
    def set_point_shape(self, shape: str):
        """Define forma dos novos pontos."""
        self.current_shape = shape
        self._update_preview()
    
    def set_point_size(self, size: int):
        """Define tamanho dos novos pontos."""
        if self.current_shape == "circle":
            self.current_radius = size
        else:
            self.current_width = size
            self.current_height = size
        self._update_preview()
    
    def set_edit_mode(self, enabled: bool):
        """Ativa/desativa modo de edição."""
        self.edit_mode = enabled
        
        # Atualiza cursor
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def set_tolerance(self, tolerance: float):
        """Atualiza tolerância e redesenha pontos."""
        self.tolerance = tolerance
        for item in self.point_items.values():
            item.set_tolerance(tolerance)
    
    def highlight_point(self, point_id: int):
        """Destaca um ponto específico."""
        if point_id in self.point_items:
            self.point_items[point_id].start_blinking()
    
    def stop_highlight_point(self, point_id: int):
        """Para destaque de um ponto."""
        if point_id in self.point_items:
            self.point_items[point_id].stop_blinking()
    
    def clear(self):
        """Limpa a view."""
        self.scene.clear()
        self.image_item = None
        self.image_pixmap = None
        self.point_items.clear()
        self.preview_item = None
        self.zoom_factor = 1.0
    
    def get_image_data(self) -> bytes:
        """Retorna dados da imagem como bytes."""
        if not self.image_pixmap:
            return b''
        
        # Converte QPixmap para bytes
        from PyQt6.QtCore import QByteArray, QBuffer
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        self.image_pixmap.save(buffer, "PNG")
        return bytes(ba)
    
    def export_image_with_points(self, file_path: str) -> bool:
        """Exporta imagem com pontos renderizados."""
        if not self.image_pixmap:
            return False
        
        try:
            # Renderiza cena inteira para novo pixmap
            target_rect = self.scene.sceneRect()
            pixmap = QPixmap(int(target_rect.width()), int(target_rect.height()))
            pixmap.fill(Qt.GlobalColor.white)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.scene.render(painter, target_rect, target_rect)
            painter.end()
            
            return pixmap.save(file_path, "PNG")
        except Exception:
            return False
    
    # Métodos de zoom e navegação
    def zoom_in(self):
        """Zoom in."""
        self._scale_view(1.25)
    
    def zoom_out(self):
        """Zoom out."""
        self._scale_view(0.8)
    
    def fit_in_view(self):
        """Ajusta imagem na view."""
        if self.image_item:
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = 1.0
    
    def rotate(self, angle: int):
        """Rotaciona view."""
        self.rotate(angle)
    
    def flip_horizontal(self):
        """Espelha horizontalmente."""
        transform = self.transform()
        transform.scale(-1, 1)
        self.setTransform(transform)
    
    def flip_vertical(self):
        """Espelha verticalmente."""
        transform = self.transform()
        transform.scale(1, -1)
        self.setTransform(transform)
    
    def _scale_view(self, factor: float):
        """Aplica fator de escala."""
        self.zoom_factor *= factor
        
        # Limita zoom (10% a 400%)
        self.zoom_factor = max(0.1, min(4.0, self.zoom_factor))
        
        # Aplica transformação
        self.setTransform(QTransform().scale(self.zoom_factor, self.zoom_factor))
    
    # Event handlers
    def wheelEvent(self, event: QWheelEvent):
        """Zoom com scroll do mouse."""
        if event.angleDelta().y() > 0:
            factor = 1.1  # Zoom in
        else:
            factor = 0.9  # Zoom out
        
        self._scale_view(factor)
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Trata clique do mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.edit_mode:
                # Inicia pan
                self.is_panning = True
                self.pan_start = event.position()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                # Modo edição - adiciona ponto
                scene_pos = self.mapToScene(event.position().toPoint())
                if self._is_point_in_image(scene_pos):
                    self.point_click_requested.emit(int(scene_pos.x()), int(scene_pos.y()))
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Trata movimento do mouse."""
        if self.is_panning:
            # Pan da imagem
            delta = event.position() - self.pan_start
            self.pan_start = event.position()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - int(delta.x()))
            v_bar.setValue(v_bar.value() - int(delta.y()))
        
        elif self.edit_mode and self.image_item:
            # Atualiza preview
            self._update_preview_position(event.position().toPoint())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Trata liberação do mouse."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor if not self.edit_mode 
                          else Qt.CursorShape.CrossCursor)
        
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Mouse entra na view."""
        if self.edit_mode:
            self._show_preview()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse sai da view."""
        self._hide_preview()
        super().leaveEvent(event)
    
    # Métodos privados
    def _is_point_in_image(self, scene_pos: QPointF) -> bool:
        """Verifica se posição está dentro da imagem."""
        if not self.image_item:
            return False
        return self.image_item.contains(scene_pos)
    
    def _show_preview(self):
        """Mostra preview do ponto."""
        if not self.preview_item and self.edit_mode:
            self.preview_item = PreviewPointItem(
                self.current_shape, 
                self.current_radius,
                self.current_width, 
                self.current_height
            )
            self.scene.addItem(self.preview_item)
    
    def _hide_preview(self):
        """Esconde preview do ponto."""
        if self.preview_item:
            self.scene.removeItem(self.preview_item)
            self.preview_item = None
    
    def _update_preview(self):
        """Atualiza configuração do preview."""
        if self.preview_item:
            self.preview_item.shape = self.current_shape
            self.preview_item.update_size(
                self.current_radius, 
                self.current_width, 
                self.current_height
            )
    
    def _update_preview_position(self, view_pos):
        """Atualiza posição do preview."""
        if self.preview_item:
            scene_pos = self.mapToScene(view_pos)
            if self._is_point_in_image(scene_pos):
                self.preview_item.setPos(scene_pos)
                self.preview_item.show()
            else:
                self.preview_item.hide()
    
    # Slots para sinais do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        if point.id not in self.point_items:
            item = PointGraphicsItem(point, self.tolerance)
            item.setPos(point.x, point.y)
            item.setZValue(1)  # Camada sobre a imagem
            self.scene.addItem(item)
            self.point_items[point.id] = item
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
        if point_id in self.point_items:
            item = self.point_items[point_id]
            self.scene.removeItem(item)
            del self.point_items[point_id]
    
    def _on_points_cleared(self):
        """Callback quando todos os pontos são removidos."""
        for item in self.point_items.values():
            self.scene.removeItem(item)
        self.point_items.clear()