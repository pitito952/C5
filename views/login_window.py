# *****************************************************************************
#
#   Sistema:    C5     -   Módulo de Caja Chica
#   Módulo:     login  -   Script de Login a la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
# *****************************************************************************
#
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class LoginWindow(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.usuario_id = None
        self.username = None
        self.rol = None
        self.caja_id = None
        self.caja_nombre = None
        
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
        query = "SELECT id, nombre FROM configuracion_caja WHERE estado = 'Activa'"
        cajas = self.db.execute_query(query)
        self.cb_caja.clear()
        if cajas:
            for caja in cajas:
                self.cb_caja.addItem(caja['nombre'], userData=caja['id'])
        else:
            self.cb_caja.addItem("Sin cajas activas")

    def verificar_credenciales(self):
        usr = self.le_usuario.text().strip()
        pwd = self.le_password.text().strip()
        caja_id = self.cb_caja.currentData()
        
        if not usr or not pwd:
            QMessageBox.warning(self, "Error", "Por favor, complete todos los campos.")
            return
            
        if not caja_id:
            QMessageBox.warning(self, "Error", "Debe existir al menos una caja activa para iniciar operaciones.")
            return
            
        # In a real app we'd compare hashes (e.g., bcrypt), but here we match the string / plain text for demo.
        # The schema uses "password_hash" column.
        query = "SELECT id, username, rol FROM usuarios WHERE username = %s AND password_hash = %s AND activo = TRUE"
        res = self.db.execute_query(query, (usr, pwd))
        
        if res:
            user_data = res[0]
            self.usuario_id = user_data['id']
            self.username = user_data['username']
            self.rol = user_data['rol']
            self.caja_id = caja_id
            self.caja_nombre = self.cb_caja.currentText()
            self.accept()
        else:
            QMessageBox.critical(self, "Acceso Denegado", "Usuario o contraseña incorrectos.")
