from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox, QHeaderView, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class CrudUsuarios(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.setWindowTitle("Gestión de Usuarios")
        self.resize(700, 500)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Administración de Usuarios")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Formulario
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.le_id = QLineEdit()
        self.le_id.setReadOnly(True)
        self.le_id.setPlaceholderText("ID Auto")
        
        self.le_username = QLineEdit()
        self.le_password = QLineEdit()
        self.le_password.setEchoMode(QLineEdit.Password)
        self.le_password.setPlaceholderText("Dejar en blanco para no cambiar")
        
        self.cb_rol = QComboBox()
        self.cb_rol.addItems(["Cajero", "Administrador"])
        
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Activo", "Inactivo"])

        form_layout.addRow("ID:", self.le_id)
        form_layout.addRow("Nombre de Usuario:", self.le_username)
        form_layout.addRow("Contraseña:", self.le_password)
        form_layout.addRow("Rol:", self.cb_rol)
        form_layout.addRow("Estado:", self.cb_estado)
        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar / Actualizar")
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        
        self.btn_guardar.clicked.connect(self.guardar_usuario)
        self.btn_limpiar.clicked.connect(self.limpiar_form)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Rol", "Estado", "Último Acceso"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.seleccionar_registro)
        layout.addWidget(self.table)

    def load_data(self):
        query = "SELECT id, username, rol, activo, ultimo_acceso FROM usuarios ORDER BY id"
        registros = self.db.execute_query(query) or []
        
        self.table.setRowCount(len(registros))
        for row_idx, row_data in enumerate(registros):
            estado = "Activo" if row_data['activo'] else "Inactivo"
            acceso = str(row_data['ultimo_acceso']) if row_data['ultimo_acceso'] else "Nunca"
            
            items = [
                str(row_data['id']),
                row_data['username'],
                row_data['rol'],
                estado,
                acceso
            ]
            
            for col_idx, val in enumerate(items):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def seleccionar_registro(self):
        selected = self.table.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        self.le_id.setText(self.table.item(row, 0).text())
        self.le_username.setText(self.table.item(row, 1).text())
        self.le_password.clear()
        
        rol = self.table.item(row, 2).text()
        self.cb_rol.setCurrentText(rol)
        
        estado = self.table.item(row, 3).text()
        self.cb_estado.setCurrentText(estado)

    def limpiar_form(self):
        self.le_id.clear()
        self.le_username.clear()
        self.le_password.clear()
        self.cb_rol.setCurrentIndex(0)
        self.cb_estado.setCurrentIndex(0)
        self.table.clearSelection()

    def guardar_usuario(self):
        uid = self.le_id.text().strip()
        username = self.le_username.text().strip()
        pwd = self.le_password.text().strip()
        rol = self.cb_rol.currentText()
        activo = True if self.cb_estado.currentText() == "Activo" else False
        
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es obligatorio.")
            return

        try:
            if uid:
                # Update
                if pwd:
                    query = "UPDATE usuarios SET username=%s, password_hash=%s, rol=%s, activo=%s WHERE id=%s"
                    params = (username, pwd, rol, activo, uid)
                else:
                    query = "UPDATE usuarios SET username=%s, rol=%s, activo=%s WHERE id=%s"
                    params = (username, rol, activo, uid)
                
                self.db.execute_query(query, params)
                QMessageBox.information(self, "Éxito", "Usuario modificado.")
            else:
                # Insert
                if not pwd:
                    QMessageBox.warning(self, "Error", "La contraseña es obligatoria para usuarios nuevos.")
                    return
                    
                query = "INSERT INTO usuarios (username, password_hash, rol, activo) VALUES (%s, %s, %s, %s)"
                self.db.execute_query(query, (username, pwd, rol, activo))
                QMessageBox.information(self, "Éxito", "Usuario creado.")
                
            self.limpiar_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
