# -*- coding: utf-8 -*-
"""
Arquivo principal (main.py) - Multímetro Inteligente v1.0
Versão corrigida para PyQt6
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Adiciona pasta src ao path para imports funcionarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import da janela principal
from src.views.main_window import MainWindow


def main():
    """Função principal da aplicação."""
    # Configura aplicação
    app = QApplication(sys.argv)
    app.setApplicationName("Multímetro Inteligente")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("MultimetroInteligente")
    
    # ✅ CORREÇÃO: Atributos corretos para PyQt6
    # Estes atributos não existem mais no PyQt6, eram do PyQt5
    # PyQt6 gerencia DPI automaticamente
    
    # Cria e mostra janela principal
    try:
        window = MainWindow()
        window.show()
        
        # Inicia loop da aplicação
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Erro ao inicializar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()