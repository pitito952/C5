# *****************************************************************************
#
#   Sistema:    C5     -   Módulo de Caja Chica
#   Módulo:     login  -   Script de Login a la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   02 |07/03/2026| Antigravity/Addy López |Implementación de bcrypt para contraseñas.
#   03 |07/03/2026| Antigravity/Addy López |Implementación de Sistema de Logs.
# *****************************************************************************
#
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import bcrypt
import logging

class LoginWindow(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        logging.info("[LOGIN] Entrando al programa (Ventana de Login).")

        self.db = db_connection
        self.le_usuario = self.le_password = self.cb_caja = self.username = None
        self.btn_ingresar = self.btn_salir = self.usuario_id = self.rol = self.caja_id = self.caja_nombre = None
        
        self.setWindowTitle("Iniciar Sesión")
        self.resize(300, 200)
        self.setModal(True)
        # Prevent closing with X to force authentication
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Módulo de Caja Chica")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        self.le_usuario = QLineEdit()
        self.le_usuario.setPlaceholderText("Nombre de usuario")
        form_layout.addRow("Usuario:", self.le_usuario)
        
        self.le_password = QLineEdit()
        self.le_password.setEchoMode(QLineEdit.Password)
        self.le_password.setPlaceholderText("Contraseña")
        form_layout.addRow("Contraseña:", self.le_password)
        
        self.cb_caja = QComboBox()
        self.cargar_cajas()
        form_layout.addRow("Caja:", self.cb_caja)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.setStyleSheet("background-color: #0d6efd; color: white; font-weight: bold;")
        self.btn_ingresar.clicked.connect(self.verificar_credenciales)
        self.btn_ingresar.setDefault(True) # Hace que Enter accione este botón
        
        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setAutoDefault(False) # Evita que tome el foco de Enter por accidente
        self.btn_salir.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_salir)
        btn_layout.addWidget(self.btn_ingresar)
        
        layout.addLayout(btn_layout)

    def cargar_cajas(self):
        try:
            query = "SELECT id, nombre FROM configuracion_caja WHERE estado = 'Activa'"
            cajas = self.db.execute_query(query)
            self.cb_caja.clear()
            if cajas:
                for caja in cajas:
                    self.cb_caja.addItem(caja['nombre'], userData=caja['id'])
            else:
                self.cb_caja.addItem("Sin cajas activas")
                logging.warning("[LOGIN] No se encontraron cajas activas en la base de datos.")
        except Exception as e:
            logging.error(f"[LOGIN] Error al cargar cajas: {e}")

    def verificar_credenciales(self):
        usr = self.le_usuario.text().strip()
        pwd = self.le_password.text().strip()
        caja_id = self.cb_caja.currentData()
        
        if not usr or not pwd:
            QMessageBox.warning(self, "Error", "Por favor, complete todos los campos.")
            logging.warning("[LOGIN] Intento de login fallido: Campos vacíos.")
            return
            
        if not caja_id:
            QMessageBox.warning(self, "Error", "Debe existir al menos una caja activa para iniciar operaciones.")
            logging.warning("[LOGIN] Intento de login fallido: No hay caja seleccionada.")
            return
            
        # 1. Buscar al usuario solo por su nombre de usuario
        query = "SELECT id, username, password_hash, rol FROM usuarios WHERE username = %s AND activo = TRUE"
        res = self.db.execute_query(query, (usr,))
        
        if res:
            user_data = res[0]
            stored_hash = user_data['password_hash']
            
            # 2. Verificar la contraseña ingresada contra el hash almacenado
            # El hash de la BD puede ser string, bcrypt necesita bytes.
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
                
            try:
                if bcrypt.checkpw(pwd.encode('utf-8'), stored_hash):
                    # Contraseña correcta: Guardar datos y aceptar el diálogo
                    self.usuario_id = user_data['id']
                    self.username = user_data['username']
                    self.rol = user_data['rol']
                    self.caja_id = caja_id
                    self.caja_nombre = self.cb_caja.currentText()
                    
                    logging.info(f"[LOGIN] Usuario '{usr}' autenticado correctamente en caja '{self.caja_nombre}'.")
                    self.accept()
                    return # Salir de la función
                else:
                    logging.warning(f"[LOGIN] Contraseña incorrecta para usuario '{usr}'.")
            except ValueError as e:
                logging.error(f"[LOGIN] Error verificando hash para usuario '{usr}': {e}")
                pass
        else:
            logging.warning(f"[LOGIN] Usuario no encontrado o inactivo: '{usr}'.")

        # Si el usuario no se encontró o la contraseña no coincidió, mostrar error.
        QMessageBox.critical(self, "Acceso Denegado", "Usuario o contraseña incorrectos.")
