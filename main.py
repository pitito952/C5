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
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from views.main_window import MainWindow
from views.login_window import LoginWindow
from database.connection import DatabaseConnection
from database.init_db import init_db

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
    """Función principal que inicia la aplicación."""
    setup_logging()
    logging.info("[MAIN] Entrando al programa.")

    app = QApplication(sys.argv)
    
    # Set global application style if needed
    app.setStyle("Fusion")
    
    try:
        # --- Verificación de la Base de Datos ---
        db_checker = DatabaseConnection()
        if not db_checker.check_database_exists():
            logging.warning("[MAIN] La base de datos no existe. Intentando crearla...")
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Asistente de Primera Ejecución")
            msg_box.setText("No se ha encontrado la base de datos. Se procederá a crearla.\n\nEste proceso solo ocurrirá una vez.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setText("Aceptar")
            msg_box.exec()
            
            init_db(ask_confirmation=False) # Ejecutar sin pedir confirmación
            
            # Volver a verificar después de la creación
            if not db_checker.check_database_exists():
                raise Exception("No se pudo crear la base de datos. Revise la conexión y los permisos.")
        
        # --- Conexión principal para la aplicación ---
        db = DatabaseConnection()
        if not db.get_connection():
            raise Exception("No se pudo establecer la conexión principal a la base de datos.")

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
        QMessageBox.critical(None, "Error Crítico", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
