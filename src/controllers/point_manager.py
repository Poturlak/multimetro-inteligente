# -*- coding: utf-8 -*-
"""
PointManager - Gerenciador de pontos de medição.

Funcionalidades principais:
- Armazenamento e gerenciamento de pontos
- Operações CRUD (Create, Read, Update, Delete)
- Sinais para notificação de mudanças
- Integração com ImageViewer e PointsTable
- Medições automáticas via hardware
- Análise de divergências e tolerâncias
"""

from typing import List, Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime

from src.models.point import Point


class PointManager(QObject):
    """
    Gerenciador central de pontos de medição.
    
    Responsável por:
    - Manter lista de pontos ordenada
    - Validar operações nos pontos
    - Notificar mudanças via sinais
    - Coordenar medições automáticas
    - Calcular estatísticas de tolerância
    """
    
    # Sinais emitidos
    point_added = pyqtSignal(Point)                       # Ponto adicionado
    point_removed = pyqtSignal(int)                       # Ponto removido (ID)
    point_updated = pyqtSignal(Point)                     # Ponto modificado
    points_cleared = pyqtSignal()                         # Todos os pontos removidos
    point_measured = pyqtSignal(int, str, float)         # Ponto medido (ID, tipo, valor)
    measurement_started = pyqtSignal(int, str)            # Medição iniciada (ID, tipo)
    measurement_completed = pyqtSignal(int)               # Medição finalizada (ID)
    statistics_changed = pyqtSignal(dict)                 # Estatísticas atualizadas
    
    def __init__(self):
        super().__init__()
        
        # Armazenamento principal
        self.points: List[Point] = []
        self.points_by_id: Dict[int, Point] = {}
        
        # Controle de IDs
        self.next_id = 1
        self.max_points = 1000  # Limite máximo de pontos
        
        # Estado do sistema
        self.edit_mode = False
        self.measurement_in_progress = False
        self.current_measurement_point: Optional[int] = None
        
        # Configurações de medição
        self.auto_measurement_enabled = False
        self.measurement_timeout = 30.0  # segundos
        self.retry_attempts = 3
        
        # Callbacks customizados
        self.measurement_callbacks: Dict[str, Callable] = {}
        
        # Timer para medições
        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self._on_measurement_timeout)
        
        # Estatísticas cache
        self.stats_cache: Optional[Dict[str, Any]] = None
        self.stats_cache_dirty = True
        
        print("✅ PointManager inicializado")
    
    # ========== OPERAÇÕES BÁSICAS DE PONTOS ==========
    
    def add_point(self, x: int, y: int, shape: str, **kwargs) -> Optional[int]:
        """
        Adiciona um novo ponto de medição.
        
        Args:
            x, y: Coordenadas na imagem
            shape: "circle" ou "rectangle"  
            **kwargs: Parâmetros adicionais (radius, width, height, etc.)
            
        Returns:
            ID do ponto criado ou None se erro
        """
        try:
            # Validações
            if len(self.points) >= self.max_points:
                print(f"❌ Limite máximo de {self.max_points} pontos atingido")
                return None
            
            if not self._validate_coordinates(x, y):
                print(f"❌ Coordenadas inválidas: ({x}, {y})")
                return None
            
            # Cria ponto
            point = Point(
                id=self.next_id,
                x=x,
                y=y,
                shape=shape,
                **kwargs
            )
            
            # Adiciona às estruturas
            self.points.append(point)
            self.points_by_id[point.id] = point
            
            # Atualiza ID para próximo ponto
            self.next_id += 1
            
            # Marca estatísticas como desatualizadas
            self.stats_cache_dirty = True
            
            # Emite sinal
            self.point_added.emit(point)
            
            # Log
            print(f"✅ Ponto #{point.id} adicionado em ({x}, {y})")
            
            return point.id
            
        except Exception as e:
            print(f"❌ Erro ao adicionar ponto: {e}")
            return None
    
    def remove_point(self, point_id: int) -> bool:
        """
        Remove um ponto pelo ID.
        
        Args:
            point_id: ID do ponto a remover
            
        Returns:
            True se removido com sucesso
        """
        try:
            # Busca ponto
            point = self.points_by_id.get(point_id)
            if not point:
                print(f"❌ Ponto #{point_id} não encontrado")
                return False
            
            # Remove das estruturas
            self.points.remove(point)
            del self.points_by_id[point_id]
            
            # Para medição se era o ponto atual
            if self.current_measurement_point == point_id:
                self._stop_current_measurement()
            
            # Marca estatísticas como desatualizadas
            self.stats_cache_dirty = True
            
            # Emite sinal
            self.point_removed.emit(point_id)
            
            # Log
            print(f"✅ Ponto #{point_id} removido")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao remover ponto #{point_id}: {e}")
            return False
    
    def update_point(self, point_id: int, **kwargs) -> bool:
        """
        Atualiza propriedades de um ponto.
        
        Args:
            point_id: ID do ponto
            **kwargs: Propriedades a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            point = self.points_by_id.get(point_id)
            if not point:
                print(f"❌ Ponto #{point_id} não encontrado")
                return False
            
            # Atualiza propriedades
            for key, value in kwargs.items():
                if hasattr(point, key):
                    setattr(point, key, value)
                else:
                    print(f"⚠️ Propriedade '{key}' não existe em Point")
            
            # Marca estatísticas como desatualizadas
            self.stats_cache_dirty = True
            
            # Emite sinal
            self.point_updated.emit(point)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar ponto #{point_id}: {e}")
            return False
    
    def clear_points(self):
        """Remove todos os pontos."""
        try:
            # Para qualquer medição em andamento
            if self.measurement_in_progress:
                self._stop_current_measurement()
            
            # Limpa estruturas
            self.points.clear()
            self.points_by_id.clear()
            
            # Reseta ID
            self.next_id = 1
            
            # Limpa cache de estatísticas
            self.stats_cache = None
            self.stats_cache_dirty = True
            
            # Emite sinal
            self.points_cleared.emit()
            
            print("✅ Todos os pontos removidos")
            
        except Exception as e:
            print(f"❌ Erro ao limpar pontos: {e}")
    
    # ========== CONSULTAS E BUSCA ==========
    
    def get_point(self, point_id: int) -> Optional[Point]:
        """Obtém ponto pelo ID."""
        return self.points_by_id.get(point_id)
    
    def get_all_points(self) -> List[Point]:
        """Obtém todos os pontos (cópia da lista)."""
        return self.points.copy()
    
    def get_points_in_area(self, x1: int, y1: int, x2: int, y2: int) -> List[Point]:
        """Obtém pontos dentro de uma área retangular."""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return [p for p in self.points 
                if min_x <= p.x <= max_x and min_y <= p.y <= max_y]
    
    def find_point_at_position(self, x: int, y: int, tolerance: int = 10) -> Optional[Point]:
        """Encontra ponto mais próximo de uma posição."""
        closest_point = None
        min_distance = float('inf')
        
        for point in self.points:
            if point.contains_point(x, y):
                return point  # Ponto exato
            
            # Calcula distância ao centro
            distance = ((point.x - x) ** 2 + (point.y - y) ** 2) ** 0.5
            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                closest_point = point
        
        return closest_point
    
    def get_points_by_shape(self, shape: str) -> List[Point]:
        """Obtém pontos de uma forma específica."""
        return [p for p in self.points if p.shape == shape]
    
    def get_measured_points(self) -> List[Point]:
        """Obtém pontos que foram medidos."""
        return [p for p in self.points if p.is_measured()]
    
    def get_unmeasured_points(self) -> List[Point]:
        """Obtém pontos ainda não medidos."""
        return [p for p in self.points if not p.is_measured()]
    
    def get_divergent_points(self, tolerance: float) -> List[Point]:
        """Obtém pontos divergentes baseado na tolerância."""
        return [p for p in self.points if p.is_divergent(tolerance)]
    
    # ========== ESTATÍSTICAS ==========
    
    def get_point_count(self) -> int:
        """Obtém número total de pontos."""
        return len(self.points)
    
    def get_measured_count(self) -> int:
        """Obtém número de pontos medidos."""
        return len(self.get_measured_points())
    
    def get_unmeasured_count(self) -> int:
        """Obtém número de pontos não medidos."""
        return len(self.get_unmeasured_points())
    
    def get_divergent_count(self, tolerance: float) -> int:
        """Obtém número de pontos divergentes."""
        return len(self.get_divergent_points(tolerance))
    
    def get_statistics(self, tolerance: float = 5.0) -> Dict[str, Any]:
        """
        Obtém estatísticas completas dos pontos.
        
        Returns:
            Dicionário com estatísticas detalhadas
        """
        if not self.stats_cache_dirty and self.stats_cache:
            return self.stats_cache
        
        total = self.get_point_count()
        measured = self.get_measured_count()
        unmeasured = self.get_unmeasured_count()
        divergent = self.get_divergent_count(tolerance)
        passed = measured - divergent
        
        measured_points = self.get_measured_points()
        
        # Estatísticas de valores
        ref_values = [p.reference_value for p in measured_points if p.reference_value is not None]
        test_values = [p.test_value for p in measured_points if p.test_value is not None]
        
        stats = {
            'total': total,
            'measured': measured,
            'unmeasured': unmeasured,
            'passed': passed,
            'divergent': divergent,
            'measurement_progress': (measured / total * 100) if total > 0 else 0,
            'pass_rate': (passed / measured * 100) if measured > 0 else 0,
            'tolerance': tolerance,
            'shapes': {
                'circles': len(self.get_points_by_shape('circle')),
                'rectangles': len(self.get_points_by_shape('rectangle'))
            }
        }
        
        # Estatísticas de valores se há pontos medidos
        if ref_values:
            stats['reference_values'] = {
                'min': min(ref_values),
                'max': max(ref_values),
                'avg': sum(ref_values) / len(ref_values)
            }
        
        if test_values:
            stats['test_values'] = {
                'min': min(test_values),
                'max': max(test_values),
                'avg': sum(test_values) / len(test_values)
            }
        
        # Cache das estatísticas
        self.stats_cache = stats
        self.stats_cache_dirty = False
        
        # Emite sinal de atualização
        self.statistics_changed.emit(stats)
        
        return stats
    
    # ========== MEDIÇÕES ==========
    
    def start_measurement_sequence(self, measurement_type: str):
        """
        Inicia sequência de medição automática.
        
        Args:
            measurement_type: "reference" ou "test"
        """
        try:
            if self.measurement_in_progress:
                print("⚠️ Medição já em andamento")
                return
            
            unmeasured = self.get_unmeasured_points()
            if not unmeasured:
                print("⚠️ Nenhum ponto para medir")
                return
            
            self.measurement_in_progress = True
            self.current_measurement_point = unmeasured[0].id
            
            print(f"🔬 Iniciando medição {measurement_type} - {len(unmeasured)} pontos")
            
            # Inicia medição do primeiro ponto
            self._start_point_measurement(self.current_measurement_point, measurement_type)
            
        except Exception as e:
            print(f"❌ Erro ao iniciar sequência de medição: {e}")
            self.measurement_in_progress = False
    
    def _start_point_measurement(self, point_id: int, measurement_type: str):
        """Inicia medição de um ponto específico."""
        try:
            point = self.get_point(point_id)
            if not point:
                print(f"❌ Ponto #{point_id} não encontrado para medição")
                return
            
            # Emite sinal de início
            self.measurement_started.emit(point_id, measurement_type)
            
            # Configura timeout
            self.measurement_timer.start(int(self.measurement_timeout * 1000))
            
            print(f"🔬 Medindo ponto #{point_id} ({measurement_type})")
            
            # TODO: Aqui seria a integração com hardware
            # Por enquanto, simula medição após 2 segundos
            QTimer.singleShot(2000, lambda: self._simulate_measurement_result(point_id, measurement_type))
            
        except Exception as e:
            print(f"❌ Erro ao iniciar medição do ponto #{point_id}: {e}")
    
    def _simulate_measurement_result(self, point_id: int, measurement_type: str):
        """Simula resultado de medição (para desenvolvimento)."""
        import random
        
        # Simula valor medido
        base_value = 10.0 + random.uniform(-2, 2)  # Valor base com variação
        noise = random.uniform(-0.5, 0.5)  # Ruído de medição
        measured_value = base_value + noise
        
        # Registra medição
        self.record_measurement(point_id, measurement_type, measured_value)
    
    def record_measurement(self, point_id: int, measurement_type: str, value: float):
        """
        Registra resultado de uma medição.
        
        Args:
            point_id: ID do ponto medido
            measurement_type: "reference" ou "test"  
            value: Valor medido
        """
        try:
            point = self.get_point(point_id)
            if not point:
                print(f"❌ Ponto #{point_id} não encontrado")
                return
            
            # Registra valor
            if measurement_type == "reference":
                point.set_reference_value(value)
            elif measurement_type == "test":
                point.set_test_value(value)
            else:
                print(f"❌ Tipo de medição inválido: {measurement_type}")
                return
            
            # Para timer se ativo
            if self.measurement_timer.isActive():
                self.measurement_timer.stop()
            
            # Marca estatísticas como desatualizadas
            self.stats_cache_dirty = True
            
            # Emite sinais
            self.point_measured.emit(point_id, measurement_type, value)
            self.point_updated.emit(point)
            
            # Finaliza medição deste ponto
            if self.current_measurement_point == point_id:
                self.measurement_completed.emit(point_id)
                self.current_measurement_point = None
                self.measurement_in_progress = False
            
            print(f"✅ Ponto #{point_id} medido: {measurement_type} = {value:.3f}")
            
        except Exception as e:
            print(f"❌ Erro ao registrar medição: {e}")
    
    def _stop_current_measurement(self):
        """Para medição atual."""
        if self.measurement_timer.isActive():
            self.measurement_timer.stop()
        
        self.measurement_in_progress = False
        self.current_measurement_point = None
        
        print("⏹️ Medição interrompida")
    
    def _on_measurement_timeout(self):
        """Callback de timeout de medição."""
        if self.current_measurement_point:
            print(f"⏰ Timeout na medição do ponto #{self.current_measurement_point}")
            
        self._stop_current_measurement()
    
    # ========== CONFIGURAÇÃO ==========
    
    def set_edit_mode(self, enabled: bool):
        """Define modo de edição."""
        self.edit_mode = enabled
        print(f"✏️ Modo de edição: {'ativado' if enabled else 'desativado'}")
    
    def set_auto_measurement(self, enabled: bool):
        """Define medição automática."""
        self.auto_measurement_enabled = enabled
    
    def set_measurement_timeout(self, timeout: float):
        """Define timeout de medição em segundos."""
        self.measurement_timeout = max(1.0, timeout)
    
    def register_measurement_callback(self, name: str, callback: Callable):
        """Registra callback personalizado de medição."""
        self.measurement_callbacks[name] = callback
    
    # ========== UTILITÁRIOS PRIVADOS ==========
    
    def _validate_coordinates(self, x: int, y: int) -> bool:
        """Valida se coordenadas são válidas."""
        return (isinstance(x, int) and isinstance(y, int) and 
                x >= 0 and y >= 0 and x <= 10000 and y <= 10000)
    
    def _get_next_id(self) -> int:
        """Obtém próximo ID disponível."""
        while self.next_id in self.points_by_id:
            self.next_id += 1
        return self.next_id
    
    # ========== SERIALIZAÇÃO ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte dados para dicionário (para salvamento)."""
        return {
            'points': [point.to_dict() for point in self.points],
            'next_id': self.next_id,
            'settings': {
                'auto_measurement': self.auto_measurement_enabled,
                'measurement_timeout': self.measurement_timeout,
                'max_points': self.max_points
            }
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Carrega dados de dicionário."""
        try:
            # Limpa dados atuais
            self.clear_points()
            
            # Carrega pontos
            for point_data in data.get('points', []):
                point = Point.from_dict(point_data)
                self.points.append(point)
                self.points_by_id[point.id] = point
                
                # Atualiza next_id
                if point.id >= self.next_id:
                    self.next_id = point.id + 1
            
            # Carrega configurações
            settings = data.get('settings', {})
            self.auto_measurement_enabled = settings.get('auto_measurement', False)
            self.measurement_timeout = settings.get('measurement_timeout', 30.0)
            self.max_points = settings.get('max_points', 1000)
            
            # Força atualização de estatísticas
            self.stats_cache_dirty = True
            
            print(f"✅ Carregados {len(self.points)} pontos")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados de pontos: {e}")