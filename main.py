"""Punto di ingresso principale per l'applicazione File Converter."""

import sys
from pathlib import Path

# Aggiungi il percorso del progetto al path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """Funzione principale di avvio dell'applicazione."""
    # Abilita scaling HiDPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("File Converter Pro")
    app.setOrganizationName("FileConverter")
    
    # Crea e mostra la finestra principale
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
