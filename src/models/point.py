# -*- coding: utf-8 -*-
"""
Point - Modelo de ponto de medição na placa eletrônica.

Funcionalidades:
- Armazenamento de coordenadas e dimensões
- Valores de medição (referência e teste)
- Cálculo de divergência baseado em tolerância
- Serialização para salvamento em projetos
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Point:
    """
    Representa um ponto de medição na placa eletrônica.
    
    Um ponto pode ser:
    - Círculo: definido por x, y, radius
    - Retângulo: definido por x, y, width, height
    
    Armazena valores de medição para comparação:
    - reference_value: valor da placa de referência (boa)
    - test_value: valor da placa sendo testada
    """
    
    # Identificação
    id: int
    
    # Posição na imagem (pixels)
    x: int
    y: int
    
    # Formato do ponto
    shape: str  # "circle" ou "rectangle"
    
    # Dimensões (pixels)
    radius: Optional[int] = field(default=None)      # Para círculos
    width: Optional[int] = field(default=None)       # Para retângulos  
    height: Optional[int] = field(default=None)      # Para retângulos
    
    # Valores de medição
    reference_value: Optional[float] = field(default=None)  # Valor da placa boa
    test_value: Optional[float] = field(default=None)       # Valor da placa teste
    
    # Metadados opcionais
    name: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    component_type: Optional[str] = field(default=None)     # Ex: "resistor", "capacitor"
    expected_value: Optional[str] = field(default=None)     # Ex: "10kΩ", "100µF"
    
    # Timestamps
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    measured_at: Optional[datetime] = field(default=None)
    
    def __post_init__(self):
        """Validação e configuração padrão após criação do ponto."""
        # Validação de forma
        if self.shape not in ["circle", "rectangle"]:
            raise ValueError(f"Forma inválida: {self.shape}. Use 'circle' ou 'rectangle'")
        
        # Configuração de dimensões padrão
        if self.shape == "circle" and self.radius is None:
            self.radius = 20  # Raio padrão de 20 pixels
        elif self.shape == "rectangle":
            if self.width is None:
                self.width = 20   # Largura padrão
            if self.height is None:
                self.height = 20  # Altura padrão
    
    # Métodos de estado
    def is_measured(self) -> bool:
        """Verifica se o ponto foi completamente medido."""
        return (self.reference_value is not None and 
                self.test_value is not None)
    
    def has_reference(self) -> bool:
        """Verifica se tem valor de referência."""
        return self.reference_value is not None
    
    def has_test_value(self) -> bool:
        """Verifica se tem valor de teste."""
        return self.test_value is not None
    
    # Métodos de análise
    def is_divergent(self, tolerance: float) -> bool:
        """
        Verifica se o ponto está fora da tolerância especificada.
        
        Args:
            tolerance: Tolerância em porcentagem (ex: 5.0 para 5%)
            
        Returns:
            True se divergente, False caso contrário
        """
        if not self.is_measured():
            return False
        
        # Caso especial: referência = 0
        if abs(self.reference_value) < 0.001:  # Praticamente zero
            return abs(self.test_value) > 0.001  # Teste deve ser também ~0
        
        # Cálculo de diferença percentual
        diff_percent = abs((self.test_value - self.reference_value) / self.reference_value) * 100
        return diff_percent > tolerance
    
    def get_difference_percent(self) -> Optional[float]:
        """
        Calcula diferença percentual entre valores.
        
        Returns:
            Diferença em porcentagem ou None se não medido
        """
        if not self.is_measured() or abs(self.reference_value) < 0.001:
            return None
        
        return ((self.test_value - self.reference_value) / self.reference_value) * 100
    
    def get_difference_absolute(self) -> Optional[float]:
        """
        Calcula diferença absoluta entre valores.
        
        Returns:
            Diferença absoluta ou None se não medido
        """
        if not self.is_measured():
            return None
        
        return self.test_value - self.reference_value
    
    def get_tolerance_status(self, tolerance: float) -> str:
        """
        Obtém status textual baseado na tolerância.
        
        Returns:
            "OK", "DIVERGENTE", "NÃO MEDIDO"
        """
        if not self.is_measured():
            return "NÃO MEDIDO"
        elif self.is_divergent(tolerance):
            return "DIVERGENTE"
        else:
            return "OK"
    
    # Métodos de medição
    def set_reference_value(self, value: float, timestamp: datetime = None):
        """Define valor de referência."""
        self.reference_value = value
        if timestamp:
            self.measured_at = timestamp
        elif self.measured_at is None:
            self.measured_at = datetime.now()
    
    def set_test_value(self, value: float, timestamp: datetime = None):
        """Define valor de teste."""
        self.test_value = value
        if timestamp:
            self.measured_at = timestamp
        elif self.measured_at is None:
            self.measured_at = datetime.now()
    
    def clear_measurements(self):
        """Remove todos os valores de medição."""
        self.reference_value = None
        self.test_value = None
        self.measured_at = None
    
    # Métodos geométricos
    def get_area(self) -> float:
        """Calcula área do ponto em pixels²."""
        if self.shape == "circle" and self.radius:
            return 3.14159 * (self.radius ** 2)
        elif self.shape == "rectangle" and self.width and self.height:
            return self.width * self.height
        return 0.0
    
    def get_center(self) -> tuple[int, int]:
        """Obtém coordenadas do centro."""
        return (self.x, self.y)
    
    def contains_point(self, px: int, py: int) -> bool:
        """Verifica se um ponto (px, py) está dentro desta forma."""
        if self.shape == "circle" and self.radius:
            distance = ((px - self.x) ** 2 + (py - self.y) ** 2) ** 0.5
            return distance <= self.radius
        elif self.shape == "rectangle" and self.width and self.height:
            half_w, half_h = self.width // 2, self.height // 2
            return (self.x - half_w <= px <= self.x + half_w and
                    self.y - half_h <= py <= self.y + half_h)
        return False
    
    # Métodos de exibição
    def get_display_name(self) -> str:
        """Obtém nome para exibição na interface."""
        if self.name:
            return f"#{self.id}: {self.name}"
        return f"Ponto #{self.id}"
    
    def get_size_text(self) -> str:
        """Obtém texto descritivo do tamanho."""
        if self.shape == "circle":
            return f"r={self.radius}px"
        else:
            return f"{self.width}x{self.height}px"
    
    def get_measurement_summary(self) -> str:
        """Obtém resumo das medições."""
        if not self.is_measured():
            return "Não medido"
        
        ref_str = f"{self.reference_value:.3f}"
        test_str = f"{self.test_value:.3f}"
        
        diff = self.get_difference_percent()
        if diff is not None:
            diff_str = f" ({diff:+.1f}%)"
        else:
            diff_str = ""
        
        return f"Ref: {ref_str} | Teste: {test_str}{diff_str}"
    
    # Serialização
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte ponto para dicionário (para salvamento).
        
        Returns:
            Dicionário com todos os dados do ponto
        """
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'shape': self.shape,
            'radius': self.radius,
            'width': self.width,
            'height': self.height,
            'reference_value': self.reference_value,
            'test_value': self.test_value,
            'name': self.name,
            'description': self.description,
            'component_type': self.component_type,
            'expected_value': self.expected_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Point':
        """
        Cria ponto a partir de dicionário.
        
        Args:
            data: Dicionário com dados do ponto
            
        Returns:
            Instância de Point
        """
        # Converte timestamps de string para datetime
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('measured_at'):
            data['measured_at'] = datetime.fromisoformat(data['measured_at'])
        
        return cls(**data)
    
    def copy(self) -> 'Point':
        """Cria cópia do ponto com novo ID."""
        data = self.to_dict()
        data['id'] = 0  # ID será definido pelo PointManager
        data['created_at'] = datetime.now().isoformat()
        data['measured_at'] = None
        return Point.from_dict(data)
    
    def __str__(self) -> str:
        """Representação textual do ponto."""
        return f"Point(id={self.id}, x={self.x}, y={self.y}, shape={self.shape})"
    
    def __repr__(self) -> str:
        """Representação técnica do ponto."""
        return (f"Point(id={self.id}, x={self.x}, y={self.y}, shape='{self.shape}', "
                f"measured={self.is_measured()})")