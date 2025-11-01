# -*- coding: utf-8 -*-
"""
Teste simples para verificar se PyQt6 funciona.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

class SimpleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teste PyQt6")
        self.setFixedSize(400, 200)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout
        layout = QVBoxLayout(central)
        label = QLabel("✅ PyQt6 funcionando!\n\nSe você vê esta janela, PyQt6 está OK.")
        label.setStyleSheet("font-size: 14px; text-align: center; padding: 20px;")
        layout.addWidget(label)

def main():
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()