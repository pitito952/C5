from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox, QHeaderView, QComboBox, QWidget, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import bcrypt
import logging

class CrudUsuarios(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        logging.info("[CRUD_USUARIOS] Entrando al programa (Gestión de Usuarios).")
        self.db = db_connection
        self.current_user_id = None # Para guardar el ID del usuario seleccionado
        self.setWindowTitle("Gestión de Usuarios")
        
        # Centrar y redimensionar
        if parent:
            self.resize(int(parent.width() * 0.7), int(parent.height() * 0.7))
            self.move(parent.geometry().center() - self.rect().center())
        else:
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
        
        self.le_username = QLineEdit()
        self.le_password = QLineEdit()
        self.le_password.setEchoMode(QLineEdit.Password)
        self.le_password.setPlaceholderText("Dejar en blanco para no cambiar")
        
        self.cb_rol = QComboBox()
        self.cb_rol.addItems(["Cajero", "Administrador"])
        
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Activo", "Inactivo"])

        form_layout.addRow("Nombre de Usuario:", self.le_username)
        form_layout.addRow("Contraseña:", self.le_password)
        form_layout.addRow("Rol:", self.cb_rol)
        form_layout.addRow("Estado:", self.cb_estado)
        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar / Actualizar")
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet("background-color: #dc3545; color: white;")

        self.btn_guardar.clicked.connect(self.guardar_usuario)
        self.btn_limpiar.clicked.connect(self.limpiar_form)
        self.btn_eliminar.clicked.connect(self.eliminar_usuario)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(4) # ID Column removed
        self.table.setHorizontalHeaderLabels(["Username", "Rol", "Estado", "Último Acceso"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.seleccionar_registro)
        layout.addWidget(self.table)

    def load_data(self):
        try:
            query = "SELECT id, username, rol, activo, ultimo_acceso FROM usuarios ORDER BY id"
            registros = self.db.execute_query(query)
            
            if registros is None:
                registros = []
                
            self.table.setRowCount(len(registros))
            for row_idx, row_data in enumerate(registros):
                estado = "Activo" if row_data['activo'] else "Inactivo"
                acceso = str(row_data['ultimo_acceso']) if row_data['ultimo_acceso'] else "Nunca"
                
                # Guardar ID en el primer item, pero no mostrarlo
                item_username = QTableWidgetItem(row_data['username'])
                item_username.setData(Qt.UserRole, row_data['id'])
                self.table.setItem(row_idx, 0, item_username)

                self.table.setItem(row_idx, 1, QTableWidgetItem(row_data['rol']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(estado))
                self.table.setItem(row_idx, 3, QTableWidgetItem(acceso))
        except Exception as e:
            logging.error(f"[CRUD_USUARIOS] Error cargando datos: {e}")

    def seleccionar_registro(self):
        selected = self.table.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        self.current_user_id = self.table.item(row, 0).data(Qt.UserRole) # Obtener ID oculto
        
        self.le_username.setText(self.table.item(row, 0).text())
        self.le_password.clear()
        
        rol = self.table.item(row, 1).text()
        self.cb_rol.setCurrentText(rol)
        
        estado = self.table.item(row, 2).text()
        self.cb_estado.setCurrentText(estado)

    def limpiar_form(self):
        self.current_user_id = None
        self.le_username.clear()
        self.le_password.clear()
        self.cb_rol.setCurrentIndex(0)
        self.cb_estado.setCurrentIndex(0)
        self.table.clearSelection()

    def guardar_usuario(self):
        uid = self.current_user_id
        username = self.le_username.text().strip()
        pwd = self.le_password.text().strip()
        rol = self.cb_rol.currentText()
        activo = 1 if self.cb_estado.currentText() == "Activo" else 0
        
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es obligatorio.")
            return

        try:
            hashed_pwd = None
            if pwd:
                salt = bcrypt.gensalt()
                hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), salt).decode('utf-8')

            if uid:
                # Update
                if pwd:
                    query = "UPDATE usuarios SET username=%s, password_hash=%s, rol=%s, activo=%s WHERE id=%s"
                    params = (username, hashed_pwd, rol, activo, uid)
                    logging.info(f"[CRUD_USUARIOS] Actualizando usuario ID {uid} con nueva contraseña.")
                else:
                    query = "UPDATE usuarios SET username=%s, rol=%s, activo=%s WHERE id=%s"
                    params = (username, rol, activo, uid)
                    logging.info(f"[CRUD_USUARIOS] Actualizando usuario ID {uid}.")
                
                self.db.execute_query(query, params)
                QMessageBox.information(self, "Éxito", "Usuario modificado.")
            else:
                # Insert
                if not pwd:
                    QMessageBox.warning(self, "Error", "La contraseña es obligatoria para usuarios nuevos.")
                    return
                    
                query = "INSERT INTO usuarios (username, password_hash, rol, activo) VALUES (%s, %s, %s, %s)"
                self.db.execute_query(query, (username, hashed_pwd, rol, activo))
                logging.info(f"[CRUD_USUARIOS] Creando nuevo usuario '{username}'.")
                QMessageBox.information(self, "Éxito", "Usuario creado.")
                
            self.limpiar_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_USUARIOS] Error guardando usuario: {e}")

    def eliminar_usuario(self):
        uid = self.current_user_id
        if not uid:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un usuario de la tabla para eliminar.")
            return

        try:
            query_check = "SELECT COUNT(*) as count FROM movimientos_caja WHERE usuario_id = %s"
            result = self.db.execute_query(query_check, (uid,))
            
            if result and result[0]['count'] > 0:
                msg = f"No se puede eliminar el usuario ID {uid} porque tiene {result[0]['count']} movimientos asociados."
                QMessageBox.critical(self, "Error de Borrado", msg)
                logging.warning(f"[CRUD_USUARIOS] Intento fallido de eliminar usuario ID {uid}: Tiene movimientos asociados.")
                return

            confirm = QMessageBox.question(self, "Confirmar Eliminación",
                                           f"¿Está seguro de que desea eliminar al usuario ID {uid}?",
                                           QMessageBox.Yes | QMessageBox.No)

            if confirm == QMessageBox.Yes:
                query_delete = "DELETE FROM usuarios WHERE id = %s"
                self.db.execute_query(query_delete, (uid,))
                logging.info(f"[CRUD_USUARIOS] Usuario ID {uid} eliminado exitosamente.")
                QMessageBox.information(self, "Éxito", "Usuario eliminado correctamente.")
                
                self.limpiar_form()
                self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_USUARIOS] Error eliminando usuario ID {uid}: {e}")
