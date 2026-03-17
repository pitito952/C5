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
from views.crud_empresa import CrudEmpresa
from views.login_window import LoginWindow
from utils.generar_huella import mostrar_huella
from utils.generador_licencias import *
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

def verificar_licencia():
    """Verifica si la licencia guardada es válida para este equipo."""
    try:
        # 1. Obtener la licencia guardada en la base de datos
        db = DatabaseConnection()
        # Es crucial que la conexción se establezca aquí para asegurar que la BBDD existe
        if not db.get_connection():
            raise Exception("No se pudo conectar a la base de datos para verificar la Licencia.")

        res = db.execute_query("SELECT clave_licencia FROM parametros_control WHERE id = 1")

        # Caso 1: La tabla o el registro no existen (no debería pasar si el init_db funcionó)
        if not res:
            return "PRIMERA_VEZ"

        licencia_guardada = res[0].get('clave_licencia')

        # Caso 2: El campo de licencia está vacío. Es la primera vez
        if not licencia_guardada:
            return "PRIMERA_VEZ"

        # Caso 3: hay una licencia, hay que verificarla
        from getmac import get_mac_address
        mac_actual = get_mac_address()
        licencia_esperada = generar_licencia(mac_actual)

        return licencia_guardada == licencia_esperada

    except Exception as e:
        logging.error(f"[LICENSE] Fallo en la verificación de licencia: {e}")
        QMessageBox.critical(None, "Error de Licencia", str(e))
        return False

def main():
    """Función principal que inicia la aplicación."""
    setup_logging()
    logging.info("[MAIN] Entrando al programa.")

    app = QApplication(sys.argv)

    # Set global application style if needed
    app.setStyle("Fusion")

    try:
        # --- 1. Verificación y Creación de la Base de Datos ---
        db_checker = DatabaseConnection()
        if not db_checker.check_database_exists():
            logging.warning("[MAIN] La base de datos no existe. Intentando crearla...")
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Asistente de Primera Ejecución")
            msg_box.setText("No se ha encontrado la base de datos. Se procederá a crearla.\n\nEste proceso solo ocurrirá una vez.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.button(QMessageBox.StandardButton.Ok).setText("Aceptar")
            msg_box.exec()
            
            init_db(ask_confirmation=False) # Ejecutar sin pedir confirmación
            
            # Volver a verificar después de la creación
            if not db_checker.check_database_exists():
                raise Exception("No se pudo crear la base de datos. Revise la conexión y los permisos.")

        # --- 2. Bucle de Verificación de Licencia ---
        #  Se ejecutará cada vez que se inicie la aplicación hasta que
        #  la licencia sea válida.
        while True:
            licencia_valida = verificar_licencia()  # Devuelve True, False o 'PRIMERA_VEZ'

            if licencia_valida is True:
                # Si la licencia es válida, salimos del bucle y continuamos a la app principal
                logging.info("[MAIN] Licencia verificada. Iniciando Login.")
                break

            elif licencia_valida == "PRIMERA_VEZ":
                # La base de datos existe, pero no hay licencia registrada.
                # Es la primera ejecución o una instalación sin licenciar.
                from getmac import get_mac_address
                mac_actual = get_mac_address()

                msg_box = QMessageBox()
                msg_box.setWindowTitle("Activación Requerida")
                msg_box.setText(f"""
                Bienvenido(a). Para activar la aplicación, por favor, siga estos pados:

                1. Envíe el siguiente CÓDIGO DE EQUIPO a su Proveedor de Software:
                    {mac_actual}
                
                2. Recibirá una CLAVE DE LICENCIA.
                
                3. Haga clic en 'Registrar Licencia' para introducir la clave recibida.
                """)
                msg_box.setIcon(QMessageBox.Icon.Information)
                registrar_btn = msg_box.addButton("Registrar Licencia", QMessageBox.AcceptRole)
                salir_btn = msg_box.addButton("Salir", QMessageBox.RejectRole)
                msg_box.exec()

                if msg_box.clickedButton() == registrar_btn:
                    # Abrir Ventana de Empresa (crud_empresa) para que el usuario pegue la clave
                    db = DatabaseConnection()
                    dialogo_empresa = CrudEmpresa(db)
                    dialogo_empresa.exec()
                    # Al cerrar, el bucle 'while' se repetirá, re-verificando la licencia.
                else:
                    # El usuario decidió salir.
                    sys.exit(0)

            else:   # licencia_valida == False
                # La licencia existe pero es incorrecta para este equipo
                from getmac import get_mac_address
                mac_actual = get_mac_address()
                QMessageBox.critical(None, "Error de Licencia",
                                     f"La licencia registrada no es válida para este equipo. \n\n"
                                     f"Huella del equipo actual: {mac_actual}\n\n"
                                     f"Por favor, contacte a Soporte Técnico o a su Proveedor de Software."
                                     )
                sys.exit(1) # salir de la aplicación

        # --- 3. Salió del bucle. Licencia válida. Continuar al Login. ---
        # Conexión principal para la aplicación
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
