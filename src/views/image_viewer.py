# -*- coding: utf-8 -*-
"""
ImageViewer - Versão com Preview CORRETO conforme specs2.docx
- ✅ Preview transparente na scene (não cursor personalizado)
- ✅ Mesmo tamanho EXATO do ponto que será criado
- ✅ Segue mouse em tempo real
- ✅ Vermelho FF0000, alpha 80 (mais transparente)
- ✅ Sem ID, apenas preview
- ✅ Desaparece ao sair da área da imagem
"""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QColor, QBrush, QWheelEvent, QPaintEvent, QFont, QCursor
import base64
from io import BytesIO

from src.controllers.point_manager import PointManager
from src.models.point import Point


class PreviewPointItem:
    """✅ NOVO: Item de preview que segue mouse conforme specs2"""
    
    def __init__(self, scene, shape: str, size: int):
        self.scene = scene
        self.shape = shape
        self.size = size
        self.graphics_item = None
        self._create_preview_item()
    
    def _create_preview_item(self):
        """Cria item gráfico de preview na scene"""
        # ✅ ESPECIFICAÇÃO: Cor Vermelho FF0000, alpha 80 (mais transparente)
        preview_color = QColor(255, 0, 0, 80)  # Vermelho transparente
        
        if self.shape == "circle":
            from PyQt6.QtWidgets import QGraphicsEllipseItem
            radius = self.size
            self.graphics_item = QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
        else:
            from PyQt6.QtWidgets import QGraphicsRectItem
            half_size = self.size // 2
            self.graphics_item = QGraphicsRectItem(-half_size, -half_size, self.size, self.size)
        
        # Configura aparência
        self.graphics_item.setBrush(QBrush(preview_color))
        self.graphics_item.setPen(QColor(255, 0, 0, 120))  # Borda um pouco mais visível
        self.graphics_item.setZValue(10)  # Fica na frente dos pontos
        
        # Adiciona à scene
        self.scene.addItem(self.graphics_item)
    
    def update_position(self, scene_pos: QPointF):
        """✅ ESPECIFICAÇÃO: Segue cursor em tempo real"""
        if self.graphics_item:
            self.graphics_item.setPos(scene_pos)
    
    def update_properties(self, shape: str, size: int):
        """Atualiza propriedades do preview"""
        if self.shape != shape or self.size != size:
            self.shape = shape
            self.size = size
            self._recreate_preview_item()
    
    def _recreate_preview_item(self):
        """Recria item de preview com novas propriedades"""
        if self.graphics_item:
            self.scene.removeItem(self.graphics_item)
        self._create_preview_item()
    
    def show(self):
        """Mostra preview"""
        if self.graphics_item:
            self.graphics_item.setVisible(True)
    
    def hide(self):
        """✅ ESPECIFICAÇÃO: Desaparece ao sair da área da imagem"""
        if self.graphics_item:
            self.graphics_item.setVisible(False)
    
    def remove(self):
        """Remove preview da scene"""
        if self.graphics_item:
            self.scene.removeItem(self.graphics_item)
            self.graphics_item = None


class ImageViewer(QGraphicsView):
    """
    ImageViewer com preview CORRETO conforme specs2.docx
    
    ✅ CORREÇÕES IMPLEMENTADAS:
    - Preview transparente na scene (não cursor personalizado)
    - Mesmo tamanho EXATO do ponto que será criado
    - Segue mouse em tempo real
    - Vermelho FF0000, alpha 80 conforme specs
    """
    
    # Sinais
    point_click_requested = pyqtSignal(int, int)  # x, y na imagem
    
    def __init__(self):
        super().__init__()
        
        # Configuração inicial
        self._setup_viewer()
        
        # Estado da imagem
        self.image_pixmap: Optional[QPixmap] = None
        self.original_pixmap: Optional[QPixmap] = None
        
        # Scene e items
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        
        # Sistema de transformações
        self.current_transform = QTransform()
        self.transform_history: List[QTransform] = []
        
        # Integração com pontos
        self.point_manager: Optional[PointManager] = None
        self.current_shape = "circle"
        self.current_size = 20  # ✅ Tamanho EXATO do ponto na imagem
        self.tolerance = 5.0
        self.edit_mode = False
        
        # ✅ NOVO: Preview conforme specs2
        self.preview_item: Optional[PreviewPointItem] = None
        self.mouse_over_image = False
        
        # Estado de interação
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        print("✅ ImageViewer com preview conforme specs2.docx")
    
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
        
        # ✅ IMPORTANTE: Habilita tracking do mouse para preview
        self.setMouseTracking(True)
    
    # ========== MÉTODOS DE TRANSFORMAÇÃO (mantidos) ==========
    
    def rotate_image(self, angle: float) -> bool:
        """Rotaciona imagem no ângulo especificado."""
        if not self.image_pixmap:
            print("❌ Nenhuma imagem carregada para rotacionar")
            return False
        
        try:
            transform = QTransform().rotate(angle)
            rotated_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            self.transform_history.append(self.current_transform)
            self.current_transform = self.current_transform * transform
            
            self._update_pixmap(rotated_pixmap)
            
            print(f"✅ Imagem rotacionada {angle}°")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rotacionar imagem: {e}")
            return False
    
    def flip_image(self, horizontal: bool) -> bool:
        """Espelha imagem horizontal ou verticalmente."""
        if not self.image_pixmap:
            print("❌ Nenhuma imagem carregada para espelhar")
            return False
        
        try:
            if horizontal:
                transform = QTransform().scale(-1, 1)
                direction = "horizontalmente"
            else:
                transform = QTransform().scale(1, -1)
                direction = "verticalmente"
            
            flipped_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            self.transform_history.append(self.current_transform)
            self.current_transform = self.current_transform * transform
            
            self._update_pixmap(flipped_pixmap)
            
            print(f"✅ Imagem espelhada {direction}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao espelhar imagem: {e}")
            return False
    
    def _update_pixmap(self, new_pixmap: QPixmap):
        """Atualiza pixmap exibido."""
        self.image_pixmap = new_pixmap
        
        if self.pixmap_item:
            self.pixmap_item.setPixmap(new_pixmap)
        else:
            self.pixmap_item = self.scene.addPixmap(new_pixmap)
        
        self._center_image()
        
        if self.point_manager:
            self._render_points()
    
    # ========== MÉTODOS ORIGINAIS ==========
    
    def set_image(self, pixmap: QPixmap):
        """Carrega nova imagem."""
        try:
            self.original_pixmap = pixmap.copy()
            self.image_pixmap = pixmap.copy()
            
            self.current_transform = QTransform()
            self.transform_history.clear()
            
            self.scene.clear()
            self.pixmap_item = None
            
            # Remove preview anterior se existir
            if self.preview_item:
                self.preview_item.remove()
                self.preview_item = None
            
            self.pixmap_item = self.scene.addPixmap(self.image_pixmap)
            
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
        
        # Remove preview
        if self.preview_item:
            self.preview_item.remove()
            self.preview_item = None
        
        print("✅ Imagem limpa")
    
    def _center_image(self):
        """Centraliza imagem na scene."""
        if self.image_pixmap:
            rect = QRectF(self.image_pixmap.rect())
            self.scene.setSceneRect(rect)
            self.centerOn(rect.center())
    
    # ========== ZOOM E NAVEGAÇÃO ==========
    
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
    
    # ========== ✅ EVENTOS DO MOUSE CORRETOS ==========
    
    def mousePressEvent(self, event):
        """Trata clique do mouse com comportamento correto."""
        if event.button() == Qt.MouseButton.LeftButton:
            
            # Verifica se deve adicionar ponto (modo marcação + edição ativa)
            if (self.edit_mode and self._is_in_marking_mode() and 
                self._is_click_on_image(event.pos())):
                
                scene_pos = self.mapToScene(event.pos())
                image_pos = scene_pos - self.pixmap_item.boundingRect().topLeft()
                x, y = int(image_pos.x()), int(image_pos.y())
                
                # Emite sinal para adicionar ponto
                self.point_click_requested.emit(x, y)
                return
            
            # Pan mode (qualquer outro caso)
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """✅ CORRIGIDO: Preview de ponto conforme specs2"""
        
        # ✅ ESPECIFICAÇÃO: Preview aparece ao mover mouse sobre imagem
        if (self.edit_mode and self._is_in_marking_mode() and 
            self._is_mouse_over_image(event.pos())):
            
            # Cria preview se não existir
            if not self.preview_item:
                self.preview_item = PreviewPointItem(self.scene, self.current_shape, self.current_size)
            
            # ✅ ESPECIFICAÇÃO: Segue cursor em tempo real
            scene_pos = self.mapToScene(event.pos())
            self.preview_item.update_position(scene_pos)
            self.preview_item.show()
            self.mouse_over_image = True
            
        else:
            # ✅ ESPECIFICAÇÃO: Desaparece ao sair da área da imagem
            if self.preview_item and self.mouse_over_image:
                self.preview_item.hide()
                self.mouse_over_image = False
        
        # Pan normal
        if self.is_panning and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Trata soltar do mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self._update_cursor_for_mode()
        
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Cursor ao entrar na área."""
        self._update_cursor_for_mode()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """✅ ESPECIFICAÇÃO: Desaparece ao sair da área da imagem"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Esconde preview ao sair do widget
        if self.preview_item:
            self.preview_item.hide()
            self.mouse_over_image = False
        
        super().leaveEvent(event)
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _is_in_marking_mode(self) -> bool:
        """Verifica se está em modo marcação."""
        # Hack temporário - em produção, receber via parâmetro
        return hasattr(self, '_marking_mode') and self._marking_mode
    
    def _is_click_on_image(self, pos) -> bool:
        """Verifica se clique foi na área da imagem."""
        if not self.pixmap_item:
            return False
        
        scene_pos = self.mapToScene(pos)
        return self.pixmap_item.boundingRect().contains(scene_pos)
    
    def _is_mouse_over_image(self, pos) -> bool:
        """Verifica se mouse está sobre a imagem."""
        return self._is_click_on_image(pos)
    
    def _update_cursor_for_mode(self):
        """Atualiza cursor baseado no modo atual."""
        if self.edit_mode and self._is_in_marking_mode():
            # Cursor padrão no modo marcação (preview é na scene)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            # Cursor normal (mão aberta para pan)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    # ========== INTEGRAÇÃO COM PONTOS ==========
    
    def set_point_manager(self, point_manager: PointManager):
        """Define gerenciador de pontos."""
        self.point_manager = point_manager
        if point_manager:
            point_manager.point_added.connect(self._on_point_added)
            point_manager.point_removed.connect(self._on_point_removed)
            point_manager.points_cleared.connect(self._on_points_cleared)
            print("✅ PointManager conectado ao ImageViewer")
    
    def set_point_shape(self, shape: str):
        """✅ ESPECIFICAÇÃO: Atualiza forma do preview"""
        self.current_shape = shape
        
        # ✅ IMPORTANTE: Atualiza preview se existir
        if self.preview_item:
            self.preview_item.update_properties(self.current_shape, self.current_size)
    
    def set_point_size(self, size: int):
        """✅ ESPECIFICAÇÃO: Atualiza tamanho do preview (mesmo do ponto)"""
        self.current_size = size
        
        # ✅ IMPORTANTE: Atualiza preview se existir
        if self.preview_item:
            self.preview_item.update_properties(self.current_shape, self.current_size)
        
        print(f"✅ Tamanho do ponto atualizado: {size}px (preview também)")
    
    def set_tolerance(self, tolerance: float):
        """Define tolerância."""
        self.tolerance = tolerance
        self._render_points()  # Re-renderiza com novas cores
    
    def set_edit_mode(self, enabled: bool):
        """Define modo de edição."""
        self.edit_mode = enabled
        
        # Hack temporário: Define se está em modo marcação
        self._marking_mode = enabled
        
        # ✅ CONTROLE DO PREVIEW
        if enabled:
            # Cria preview se não existir
            if not self.preview_item:
                self.preview_item = PreviewPointItem(self.scene, self.current_shape, self.current_size)
                self.preview_item.hide()  # Inicialmente oculto
        else:
            # Remove preview ao sair do modo marcação
            if self.preview_item:
                self.preview_item.remove()
                self.preview_item = None
        
        # Atualiza cursor
        self._update_cursor_for_mode()
        
        print(f"✅ Modo edição: {'ativado' if enabled else 'desativado'}")
    
    def _render_points(self):
        """Renderiza pontos no estilo original (vermelhos com ID)."""
        if not self.point_manager or not self.pixmap_item:
            return
        
        # Remove pontos existentes da scene
        for item in self.scene.items():
            if hasattr(item, 'is_point_item'):
                self.scene.removeItem(item)
        
        # Adiciona todos os pontos
        for point in self.point_manager.get_all_points():
            self._add_point_to_scene_original_style(point)
    
    def _add_point_to_scene_original_style(self, point: Point):
        """Adiciona ponto com estilo ORIGINAL (vermelho com ID)."""
        if not self.pixmap_item:
            return
        
        try:
            # Posição na scene (relativa ao pixmap)
            scene_x = self.pixmap_item.boundingRect().x() + point.x
            scene_y = self.pixmap_item.boundingRect().y() + point.y
            
            # Cor vermelha (estilo original)
            point_color = QColor(255, 0, 0, 200)  # Vermelho opaco
            text_color = QColor(255, 255, 255)    # Texto branco
            
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
            
            # Configura aparência (estilo original)
            item.setBrush(QBrush(point_color))
            item.setPen(QColor(150, 0, 0))  # Borda mais escura
            item.is_point_item = True
            item.point_id = point.id
            item.setZValue(1)  # Pontos ficam atrás do preview
            
            self.scene.addItem(item)
            
            # Adiciona texto com ID (estilo original)
            from PyQt6.QtWidgets import QGraphicsTextItem
            text_item = QGraphicsTextItem(str(point.id))
            text_item.setDefaultTextColor(text_color)
            
            # Font bold para melhor visibilidade
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            text_item.setFont(font)
            
            # Centraliza texto no ponto
            text_rect = text_item.boundingRect()
            text_x = scene_x - text_rect.width() / 2
            text_y = scene_y - text_rect.height() / 2
            text_item.setPos(text_x, text_y)
            
            # Marca como item de ponto para identificação
            text_item.is_point_item = True
            text_item.point_id = point.id
            text_item.setZValue(2)  # Texto fica na frente dos pontos
            
            self.scene.addItem(text_item)
            
        except Exception as e:
            print(f"❌ Erro ao adicionar ponto #{point.id} à scene: {e}")
    
    def highlight_point(self, point_id: int):
        """Destaca ponto específico."""
        # TODO: Implementar highlight visual
        print(f"✅ Destacando ponto #{point_id}")
    
    # Callbacks do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        self._add_point_to_scene_original_style(point)
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
        # Remove da scene
        items_to_remove = []
        for item in self.scene.items():
            if hasattr(item, 'point_id') and item.point_id == point_id:
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.scene.removeItem(item)
    
    def _on_points_cleared(self):
        """Callback quando pontos são limpos."""
        self._render_points()
    
    # ========== EXPORT COM PONTOS ==========
    
    def export_image_with_points(self, file_path: str) -> bool:
        """Exporta imagem atual com pontos renderizados."""
        if not self.image_pixmap:
            print("❌ Nenhuma imagem para exportar")
            return False
        
        try:
            # Cria cópia da imagem atual
            export_pixmap = self.image_pixmap.copy()
            
            # Renderiza pontos na imagem (estilo original)
            if self.point_manager:
                painter = QPainter(export_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                for point in self.point_manager.get_all_points():
                    # Cor vermelha (estilo original)
                    point_color = QColor(255, 0, 0, 200)
                    text_color = QColor(255, 255, 255)
                    
                    painter.setBrush(QBrush(point_color))
                    painter.setPen(QColor(150, 0, 0))
                    
                    # Desenha forma
                    if point.shape == "circle":
                        radius = point.radius or 20
                        painter.drawEllipse(point.x - radius, point.y - radius, radius * 2, radius * 2)
                    else:
                        width = point.width or 20
                        height = point.height or 20
                        painter.drawRect(point.x - width//2, point.y - height//2, width, height)
                    
                    # Desenha ID do ponto
                    painter.setPen(text_color)
                    font = QFont()
                    font.setBold(True)
                    font.setPointSize(10)
                    painter.setFont(font)
                    painter.drawText(point.x - 5, point.y + 5, str(point.id))
                
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
        """Obtém dados da imagem atual como string base64."""
        if not self.image_pixmap:
            return None
        
        try:
            byte_array = BytesIO()
            self.image_pixmap.save(byte_array, "PNG")
            image_data = base64.b64encode(byte_array.getvalue()).decode()
            return image_data
            
        except Exception as e:
            print(f"❌ Erro ao obter dados da imagem: {e}")
            return None