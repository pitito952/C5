# *****************************************************************************
#
#   Sistema:    C5    -   Módulo de Caja Chica
#   Módulo:     main  -   Script de Entrada a la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
# *****************************************************************************
#
import sys
from PySide6.QtWidgets import QApplication, QDialog
from views.main_window import MainWindow
from views.login_window import LoginWindow
from database.connection import DatabaseConnection

def main():
    app = QApplication(sys.argv)
    
    # Set global application style if needed
    app.setStyle("Fusion")
    
    db = DatabaseConnection()
    
    # Show Login First
    login = LoginWindow(db)
    result = login.exec()
    
    if result == QDialog.Accepted:
        # Proceed with main application
        window = MainWindow(login.usuario_id, login.username, login.rol, login.caja_id, login.caja_nombre)
        window.show()
        sys.exit(app.exec())
    else:
        # User canceled login or closed window
        sys.exit(0)

if __name__ == "__main__":
    main()
