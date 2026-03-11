# *****************************************************************************
#
#   Sistema:    C5     -   Módulo de Caja Chica
#   Módulo:     login  -   Script de Login a la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   ...
#   04 |07/03/2026| Antigravity/Addy López |Mejora de UX en el botón de Ingresar.
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
        self.resize(300, 220)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self.setup_ui()
        self.actualizar_estado_boton() # Establecer estado inicial del botón

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
        self.btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd; 
                color: white; 
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        self.btn_ingresar.clicked.connect(self.verificar_credenciales)
        
        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setAutoDefault(False)
        self.btn_salir.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_salir)
        btn_layout.addWidget(self.btn_ingresar)
        
        layout.addLayout(btn_layout)

        # --- Conexiones de señales para UX ---
        # Al presionar Enter en usuario, saltar a contraseña
        self.le_usuario.returnPressed.connect(self.le_password.setFocus)
        
        # Actualizar estado del botón cuando el texto cambie en cualquiera de los campos
        self.le_usuario.textChanged.connect(self.actualizar_estado_boton)
        self.le_password.textChanged.connect(self.actualizar_estado_boton)

    def actualizar_estado_boton(self):
        """
        Habilita o deshabilita el botón 'Ingresar' basado en si los campos
        de usuario y contraseña tienen texto.
        """
        usuario_ok = len(self.le_usuario.text().strip()) > 0
        password_ok = len(self.le_password.text().strip()) > 0
        
        if usuario_ok and password_ok:
            self.btn_ingresar.setEnabled(True)
            self.btn_ingresar.setDefault(True)
        else:
            self.btn_ingresar.setEnabled(False)
            self.btn_ingresar.setDefault(False)

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
            
        query = "SELECT id, username, password_hash, rol FROM usuarios WHERE username = %s AND activo = TRUE"
        res = self.db.execute_query(query, (usr,))
        
        if res:
            user_data = res[0]
            stored_hash = user_data['password_hash']
            
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
                
            try:
                if bcrypt.checkpw(pwd.encode('utf-8'), stored_hash):
                    self.usuario_id = user_data['id']
                    self.username = user_data['username']
                    self.rol = user_data['rol']
                    self.caja_id = caja_id
                    self.caja_nombre = self.cb_caja.currentText()
                    
                    logging.info(f"[LOGIN] Usuario '{usr}' autenticado correctamente en caja '{self.caja_nombre}'.")
                    self.accept()
                    return
                else:
                    logging.warning(f"[LOGIN] Contraseña incorrecta para usuario '{usr}'.")
            except ValueError as e:
                logging.error(f"[LOGIN] Error verificando hash para usuario '{usr}': {e}")
                pass
        else:
            logging.warning(f"[LOGIN] Usuario no encontrado o inactivo: '{usr}'.")

        QMessageBox.critical(self, "Acceso Denegado", "Usuario o contraseña incorrectos.")
