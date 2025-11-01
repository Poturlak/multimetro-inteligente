# -*- coding: utf-8 -*-
"""
ImageViewer - Versão CORRIGIDA FINAL - Erro PyQt6 corrigido
- ✅ Cursor volta ao comportamento original (segue mouse)
- ✅ Preview centralizado aparece APENAS por 1 segundo após alterar tamanho
- ✅ Comportamento original restaurado conforme specs2
- 🔧 CORRIGIDO: SmoothPixmapTransform (PyQt6)
"""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QColor, QBrush, QWheelEvent, QPaintEvent, QFont, QCursor, QPen
import base64
from io import BytesIO
from copy import deepcopy

from src.controllers.point_manager import PointManager
from src.models.point import Point


class TransformationHistory:
    """Gerenciamento de histórico de transformações."""
    
    def __init__(self, max_size: int = 20):
        self.history: List[Tuple[QPixmap, str]] = []
        self.current_index = -1
        self.max_size = max_size
    
    def add_transformation(self, pixmap: QPixmap, description: str):
        """Adiciona transformação ao histórico."""
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append((pixmap.copy(), description))
        self.current_index += 1
        
        if len(self.history) > self.max_size:
            self.history.pop(0)
            self.current_index -= 1
    
    def can_undo(self) -> bool:
        """Verifica se pode desfazer."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Verifica se pode refazer."""
        return self.current_index < len(self.history) - 1
    
    def undo(self) -> Optional[Tuple[QPixmap, str]]:
        """Desfaz última transformação."""
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
    
    def redo(self) -> Optional[Tuple[QPixmap, str]]:
        """Refaz transformação desfeita."""
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def clear(self):
        """Limpa histórico."""
        self.history.clear()
        self.current_index = -1
    
    def set_initial_state(self, pixmap: QPixmap):
        """Define estado inicial."""
        self.clear()
        self.add_transformation(pixmap, "Estado inicial")


class CropSelectionItem(QGraphicsRectItem):
    """Item gráfico para seleção de recorte VERMELHA."""
    
    def __init__(self):
        super().__init__()
        self.setZValue(100)  # Fica na frente de tudo
        
        # Estilo VERMELHO
        pen = QPen(QColor(255, 0, 0, 120), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        
        # Fundo VERMELHO semi-transparente
        brush = QBrush(QColor(255, 0, 0, 80))
        self.setBrush(brush)


class PreviewPointItem:
    """✅ CORRIGIDO: Preview que segue mouse (comportamento original) + centralizado temporário."""
    
    def __init__(self, scene, shape: str, size: int, viewer_widget):
        self.scene = scene
        self.shape = shape
        self.size = size
        self.viewer_widget = viewer_widget
        self.graphics_item = None
        self._create_preview_item()
    
    def _create_preview_item(self):
        """Cria item gráfico de preview na scene"""
        # Cor Vermelho FF0000, alpha 80 (conforme specs2)
        preview_color = QColor(255, 0, 0, 80)
        
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
        self.graphics_item.setPen(QColor(255, 0, 0, 120))
        self.graphics_item.setZValue(10)  # Fica na frente dos pontos
        
        # Adiciona à scene
        self.scene.addItem(self.graphics_item)
    
    def update_position(self, scene_pos: QPointF):
        """✅ RESTAURADO: Segue cursor em tempo real (comportamento original)"""
        if self.graphics_item:
            self.graphics_item.setPos(scene_pos)
    
    def show_centered_preview(self):
        """✅ NOVO: Mostra preview centralizado por 1 segundo."""
        if self.graphics_item and hasattr(self.viewer_widget, 'pixmap_item') and self.viewer_widget.pixmap_item:
            # Centraliza
            image_rect = self.viewer_widget.pixmap_item.boundingRect()
            center_pos = image_rect.center()
            self.graphics_item.setPos(center_pos)
            self.graphics_item.setVisible(True)
    
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
        """Mostra preview (no modo normal, segue mouse)"""
        if self.graphics_item:
            self.graphics_item.setVisible(True)
    
    def hide(self):
        """Esconde preview."""
        if self.graphics_item:
            self.graphics_item.setVisible(False)
    
    def remove(self):
        """Remove preview da scene"""
        if self.graphics_item:
            self.scene.removeItem(self.graphics_item)
            self.graphics_item = None


class ImageViewer(QGraphicsView):
    """
    ImageViewer CORRIGIDO FINAL:
    - ✅ Cursor segue mouse (comportamento original)
    - ✅ Preview centralizado apenas 1 segundo após alterar tamanho
    - 🔧 CORRIGIDO: SmoothPixmapTransform (PyQt6)
    """
    
    # Sinais
    point_click_requested = pyqtSignal(int, int)  # x, y na imagem
    transformation_applied = pyqtSignal(str)       # Sinal de transformação
    
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
        
        # Sistema de transformações com histórico
        self.transformation_history = TransformationHistory()
        
        # Integração com pontos
        self.point_manager: Optional[PointManager] = None
        self.current_shape = "circle"
        self.current_size = 20  
        self.tolerance = 5.0
        self.edit_mode = False
        
        # ✅ CORRIGIDO: Preview com comportamento original + timer para centralizado
        self.preview_item: Optional[PreviewPointItem] = None
        self.mouse_over_image = False
        
        # ✅ NOVO: Timer para preview centralizado (1 segundo)
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._hide_centered_preview)
        
        # Estado de recorte (com seleção vermelha)
        self.crop_mode = False
        self.crop_selection: Optional[CropSelectionItem] = None
        self.crop_start_pos: Optional[QPointF] = None
        
        # Estado de interação
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        print("✅ ImageViewer CORRIGIDO - cursor original + preview temporário")
    
    def _setup_viewer(self):
        """🔧 CORRIGIDO: Configuração inicial do viewer com nome correto PyQt6."""
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # 🔧 CORRIGIDO: Nome correto no PyQt6
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Fundo cinza claro
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        
        # Zoom limits
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.zoom_factor = 1.15
        
        # Habilita tracking do mouse
        self.setMouseTracking(True)
    
    # ========== MÉTODOS DE TRANSFORMAÇÃO (mantidos) ==========
    
    def rotate_image(self, angle: float) -> bool:
        """Rotaciona imagem apenas 90°."""
        if not self.image_pixmap:
            print("❌ Nenhuma imagem carregada para rotacionar")
            return False
        
        try:
            if angle != 90:
                print(f"❌ Ângulo não suportado: {angle}. Apenas 90° é permitido.")
                return False
            
            transform = QTransform().rotate(90)
            description = "Rotação 90°"
            
            rotated_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # Salva no histórico
            self.transformation_history.add_transformation(self.image_pixmap, f"Antes {description}")
            
            # Atualiza imagem
            self._update_pixmap(rotated_pixmap)
            
            # Emite sinal
            self.transformation_applied.emit(description)
            
            print(f"✅ {description} aplicada")
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
                description = "Espelhamento Horizontal"
            else:
                transform = QTransform().scale(1, -1)
                description = "Espelhamento Vertical"
            
            flipped_pixmap = self.image_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # Salva no histórico
            self.transformation_history.add_transformation(self.image_pixmap, f"Antes {description}")
            
            # Atualiza imagem
            self._update_pixmap(flipped_pixmap)
            
            # Emite sinal
            self.transformation_applied.emit(description)
            
            print(f"✅ {description} aplicado")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao espelhar imagem: {e}")
            return False
    
    def start_crop_mode(self) -> bool:
        """Inicia modo de recorte com seleção vermelha."""
        if not self.image_pixmap:
            return False
        
        self.crop_mode = True
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Remove seleção anterior se existir
        if self.crop_selection:
            self.scene.removeItem(self.crop_selection)
        
        print("✅ Modo recorte ativado - seleção vermelha")
        return True
    
    def resize_image(self, new_width: int, new_height: int) -> bool:
        """Redimensiona imagem."""
        if not self.image_pixmap:
            return False
        
        try:
            # Salva no histórico
            self.transformation_history.add_transformation(self.image_pixmap, "Antes Redimensionamento")
            
            # Redimensiona
            resized_pixmap = self.image_pixmap.scaled(
                new_width, new_height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Atualiza imagem
            self._update_pixmap(resized_pixmap)
            
            # Emite sinal
            self.transformation_applied.emit(f"Redimensionamento para {new_width}x{new_height}")
            
            print(f"✅ Imagem redimensionada para {new_width}x{new_height}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao redimensionar imagem: {e}")
            return False
    
    def undo_transformation(self) -> bool:
        """Desfaz última transformação."""
        result = self.transformation_history.undo()
        if result:
            pixmap, description = result
            self._update_pixmap(pixmap)
            print(f"✅ Desfeita transformação: {description}")
            return True
        return False
    
    def redo_transformation(self) -> bool:
        """Refaz transformação desfeita."""
        result = self.transformation_history.redo()
        if result:
            pixmap, description = result
            self._update_pixmap(pixmap)
            print(f"✅ Refeita transformação: {description}")
            return True
        return False
    
    def can_undo(self) -> bool:
        """Verifica se pode desfazer."""
        return self.transformation_history.can_undo()
    
    def can_redo(self) -> bool:
        """Verifica se pode refazer."""
        return self.transformation_history.can_redo()
    
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
            
            # Configura histórico de transformações
            self.transformation_history.set_initial_state(pixmap)
            
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
        
        # Limpa histórico
        self.transformation_history.clear()
        
        # Remove preview
        if self.preview_item:
            self.preview_item.remove()
            self.preview_item = None
        
        # Para timer se estiver rodando
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        
        # Sai do modo recorte
        self.crop_mode = False
        self.crop_selection = None
        
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
    
    # ========== ✅ EVENTOS DO MOUSE CORRIGIDOS ==========
    
    def mousePressEvent(self, event):
        """Trata clique do mouse com recorte e marcação."""
        if event.button() == Qt.MouseButton.LeftButton:
            
            # Modo recorte
            if self.crop_mode and self._is_click_on_image(event.pos()):
                self._start_crop_selection(event.pos())
                return
            
            # Modo marcação
            if (self.edit_mode and self._is_in_marking_mode() and 
                self._is_click_on_image(event.pos())):
                
                scene_pos = self.mapToScene(event.pos())
                image_pos = scene_pos - self.pixmap_item.boundingRect().topLeft()
                x, y = int(image_pos.x()), int(image_pos.y())
                
                self.point_click_requested.emit(x, y)
                return
            
            # Pan mode
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """✅ CORRIGIDO: Preview segue mouse (comportamento original)"""
        
        # Atualiza seleção de recorte
        if self.crop_mode and self.crop_selection and event.buttons() == Qt.MouseButton.LeftButton:
            self._update_crop_selection(event.pos())
            return
        
        # ✅ CORRIGIDO: Preview segue mouse conforme specs2 original
        if (self.edit_mode and self._is_in_marking_mode() and 
            self._is_mouse_over_image(event.pos())):
            
            # Cria preview se não existir
            if not self.preview_item:
                self.preview_item = PreviewPointItem(self.scene, self.current_shape, self.current_size, self)
            
            # ✅ RESTAURADO: Preview segue cursor em tempo real
            scene_pos = self.mapToScene(event.pos())
            self.preview_item.update_position(scene_pos)
            self.preview_item.show()
            self.mouse_over_image = True
            
        else:
            # ✅ RESTAURADO: Desaparece ao sair da área da imagem
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
        """Trata soltar do mouse com recorte."""
        if event.button() == Qt.MouseButton.LeftButton:
            
            # Finaliza recorte
            if self.crop_mode and self.crop_selection:
                self._finish_crop_selection()
                return
            
            self.is_panning = False
            self._update_cursor_for_mode()
        
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Cursor ao entrar na área."""
        self._update_cursor_for_mode()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """✅ RESTAURADO: Desaparece ao sair da área da imagem"""
        if not self.crop_mode:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Esconde preview ao sair do widget
        if self.preview_item:
            self.preview_item.hide()
            self.mouse_over_image = False
        
        super().leaveEvent(event)
    
    # ========== MÉTODOS DE RECORTE COM SELEÇÃO VERMELHA ==========
    
    def _start_crop_selection(self, pos):
        """Inicia seleção de recorte vermelha."""
        scene_pos = self.mapToScene(pos)
        self.crop_start_pos = scene_pos
        
        # Cria item de seleção VERMELHO
        self.crop_selection = CropSelectionItem()
        self.crop_selection.setRect(QRectF(scene_pos, scene_pos))
        self.scene.addItem(self.crop_selection)
    
    def _update_crop_selection(self, pos):
        """Atualiza seleção de recorte."""
        if not self.crop_selection or not self.crop_start_pos:
            return
        
        scene_pos = self.mapToScene(pos)
        
        # Calcula retângulo
        rect = QRectF(self.crop_start_pos, scene_pos).normalized()
        
        # Limita à área da imagem
        if self.pixmap_item:
            image_rect = self.pixmap_item.boundingRect()
            rect = rect.intersected(image_rect)
        
        self.crop_selection.setRect(rect)
    
    def _finish_crop_selection(self):
        """Finaliza seleção de recorte."""
        if not self.crop_selection or not self.pixmap_item:
            return
        
        # Obtém retângulo de seleção
        selection_rect = self.crop_selection.rect()
        image_rect = self.pixmap_item.boundingRect()
        
        # Converte para coordenadas da imagem
        relative_rect = QRectF(
            selection_rect.x() - image_rect.x(),
            selection_rect.y() - image_rect.y(),
            selection_rect.width(),
            selection_rect.height()
        )
        
        # Verifica se seleção é válida
        if relative_rect.width() > 20 and relative_rect.height() > 20:
            self._apply_crop(relative_rect)
        
        # Limpa seleção
        self.scene.removeItem(self.crop_selection)
        self.crop_selection = None
        self.crop_start_pos = None
        self.crop_mode = False
        self._update_cursor_for_mode()
    
    def _apply_crop(self, rect: QRectF):
        """Aplica recorte na região selecionada."""
        try:
            # Salva no histórico
            self.transformation_history.add_transformation(self.image_pixmap, "Antes Recorte")
            
            # Recorta imagem
            cropped_pixmap = self.image_pixmap.copy(rect.toRect())
            
            # Atualiza imagem
            self._update_pixmap(cropped_pixmap)
            
            # Emite sinal
            self.transformation_applied.emit(f"Recorte {rect.width():.0f}x{rect.height():.0f}")
            
            print(f"✅ Recorte aplicado: {rect.width():.0f}x{rect.height():.0f}")
            
        except Exception as e:
            print(f"❌ Erro ao recortar: {e}")
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _is_in_marking_mode(self) -> bool:
        """Verifica se está em modo marcação."""
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
        """✅ CORRIGIDO: Cursor baseado no modo (original)."""
        if self.crop_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.edit_mode and self._is_in_marking_mode():
            # ✅ RESTAURADO: Cursor cruz no modo marcação (não personalizado)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    # ========== ✅ MÉTODOS DE PREVIEW TEMPORÁRIO ==========
    
    def _show_temporary_centered_preview(self):
        """✅ NOVO: Mostra preview centralizado por 1 segundo."""
        if not self.preview_item:
            self.preview_item = PreviewPointItem(self.scene, self.current_shape, self.current_size, self)
        
        # Para o timer se estiver rodando
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        
        # Mostra preview centralizado
        self.preview_item.show_centered_preview()
        
        # Inicia timer de 1 segundo
        self.preview_timer.start(1000)  # 1 segundo
        
        print("✅ Preview centralizado por 1 segundo")
    
    def _hide_centered_preview(self):
        """✅ NOVO: Esconde preview após timer."""
        if self.preview_item:
            self.preview_item.hide()
        print("✅ Preview centralizado ocultado")
    
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
        """✅ CORRIGIDO: Atualiza forma e mostra preview temporário."""
        self.current_shape = shape
        if self.preview_item:
            self.preview_item.update_properties(self.current_shape, self.current_size)
        
        # ✅ NOVO: Mostra preview centralizado por 1 segundo
        if self.edit_mode and self._is_in_marking_mode():
            self._show_temporary_centered_preview()
    
    def set_point_size(self, size: int):
        """✅ CORRIGIDO: Atualiza tamanho e mostra preview temporário."""
        self.current_size = size
        if self.preview_item:
            self.preview_item.update_properties(self.current_shape, self.current_size)
        
        # ✅ NOVO: Mostra preview centralizado por 1 segundo ao alterar tamanho
        if self.edit_mode and self._is_in_marking_mode():
            self._show_temporary_centered_preview()
        
        print(f"✅ Tamanho do ponto atualizado: {size}px (preview 1s)")
    
    def set_tolerance(self, tolerance: float):
        """Define tolerância."""
        self.tolerance = tolerance
        self._render_points()
    
    def set_edit_mode(self, enabled: bool):
        """Define modo de edição."""
        self.edit_mode = enabled
        self._marking_mode = enabled
        
        if enabled:
            # Cria preview (passa referência do viewer)
            if not self.preview_item:
                self.preview_item = PreviewPointItem(self.scene, self.current_shape, self.current_size, self)
                self.preview_item.hide()
        else:
            if self.preview_item:
                self.preview_item.remove()
                self.preview_item = None
            
            # Para timer se estiver rodando
            if self.preview_timer.isActive():
                self.preview_timer.stop()
        
        self._update_cursor_for_mode()
        print(f"✅ Modo edição: {'ativado' if enabled else 'desativado'} (cursor original)")
    
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
            point_color = QColor(255, 0, 0, 200)
            text_color = QColor(255, 255, 255)
            
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
            item.setPen(QColor(150, 0, 0))
            item.is_point_item = True
            item.point_id = point.id
            item.setZValue(1)
            
            self.scene.addItem(item)
            
            # Adiciona texto com ID (estilo original)
            from PyQt6.QtWidgets import QGraphicsTextItem
            text_item = QGraphicsTextItem(str(point.id))
            text_item.setDefaultTextColor(text_color)
            
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            text_item.setFont(font)
            
            # Centraliza texto no ponto
            text_rect = text_item.boundingRect()
            text_x = scene_x - text_rect.width() / 2
            text_y = scene_y - text_rect.height() / 2
            text_item.setPos(text_x, text_y)
            
            text_item.is_point_item = True
            text_item.point_id = point.id
            text_item.setZValue(2)
            
            self.scene.addItem(text_item)
            
        except Exception as e:
            print(f"❌ Erro ao adicionar ponto #{point.id} à scene: {e}")
    
    def highlight_point(self, point_id: int):
        """Destaca ponto específico."""
        print(f"✅ Destacando ponto #{point_id}")
    
    # Callbacks do PointManager
    def _on_point_added(self, point: Point):
        """Callback quando ponto é adicionado."""
        self._add_point_to_scene_original_style(point)
    
    def _on_point_removed(self, point_id: int):
        """Callback quando ponto é removido."""
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
            export_pixmap = self.image_pixmap.copy()
            
            if self.point_manager:
                painter = QPainter(export_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                for point in self.point_manager.get_all_points():
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