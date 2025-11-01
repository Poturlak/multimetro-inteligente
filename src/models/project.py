# -*- coding: utf-8 -*-
"""
BoardProject - Modelo de projeto - Versão temporária simplificada.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BoardProject:
    """
    Representa um projeto de análise de placa.
    """
    
    name: str
    board_model: str = "Modelo Desconhecido"
    is_fully_functional: bool = True
    
    # Metadata
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicialização após criação."""
        if self.created_at is None:
            self.created_at = datetime.now()
        self.modified_at = datetime.now()
    
    def mark_modified(self):
        """Marca projeto como modificado."""
        self.modified_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'name': self.name,
            'board_model': self.board_model,
            'is_fully_functional': self.is_fully_functional,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None
        }