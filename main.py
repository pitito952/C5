# *****************************************************************************
#
#   Sistema:    C5    -   Módulo de Caja Chica
#   Módulo:     main  -   Script de Entrada a la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   02 |07/03/2026| Antigravity/Addy López |Implementación de Sistema de Logs.
# *****************************************************************************
#
import sys
import os
import logging
from datetime import datetime
from PySide6.QtWidgets import QApplication, QDialog
from views.main_window import MainWindow
from views.login_window import LoginWindow
from database.connection import DatabaseConnection

def setup_logging():
    """Configura el sistema de logging."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = datetime.now().strftime("app_%Y-%m-%d.log")
    log_path = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )
    # También agregar un handler para ver los logs en la consola mientras desarrollamos
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def main():
    setup_logging()
    logging.info("[MAIN] Entrando al programa.")

    app = QApplication(sys.argv)
    
    # Set global application style if needed
    app.setStyle("Fusion")
    
    try:
        db = DatabaseConnection()
        
        # Show Login First
        logging.info("[MAIN] Iniciando ventana de Login.")
        login = LoginWindow(db)
        result = login.exec()
        
        if result == QDialog.Accepted:
            # Proceed with main application
            logging.info(f"[MAIN] Login exitoso. Usuario: {login.username}. Iniciando ventana principal.")
            window = MainWindow(login.usuario_id, login.username, login.rol, login.caja_id, login.caja_nombre)
            window.show()
            sys.exit(app.exec())
        else:
            # User canceled login or closed window
            logging.info("[MAIN] Login cancelado o cerrado por el usuario. Saliendo.")
            sys.exit(0)
    except Exception as e:
        logging.critical(f"[MAIN] Error crítico no controlado: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
