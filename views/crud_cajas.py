from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox, QHeaderView, QComboBox, QWidget, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

class CrudCajas(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        logging.info("[CRUD_CAJAS] Entrando al programa (Gestión de Cajas).")
        self.db = db_connection
        self.current_caja_id = None
        self.setWindowTitle("Gestión de Cajas")
        
        if parent:
            self.resize(int(parent.width() * 0.7), int(parent.height() * 0.7))
            self.move(parent.geometry().center() - self.rect().center())
        else:
            self.resize(600, 400)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Administración de Cajas (Puntos de Venta)")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Formulario
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.le_nombre = QLineEdit()
        self.le_descripcion = QLineEdit()
        
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Activa", "Inactiva"])

        form_layout.addRow("Nombre Caja:", self.le_nombre)
        form_layout.addRow("Descripción:", self.le_descripcion)
        form_layout.addRow("Estado:", self.cb_estado)
        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar / Actualizar")
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet("background-color: #dc3545; color: white;")

        self.btn_guardar.clicked.connect(self.guardar_caja)
        self.btn_limpiar.clicked.connect(self.limpiar_form)
        self.btn_eliminar.clicked.connect(self.eliminar_caja)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3) # ID Column removed
        self.table.setHorizontalHeaderLabels(["Nombre", "Descripción", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.seleccionar_registro)
        layout.addWidget(self.table)

    def load_data(self):
        try:
            query = "SELECT id, nombre, descripcion, estado FROM configuracion_caja ORDER BY id"
            registros = self.db.execute_query(query) or []
            
            self.table.setRowCount(len(registros))
            for row_idx, row_data in enumerate(registros):
                item_nombre = QTableWidgetItem(row_data['nombre'])
                item_nombre.setData(Qt.UserRole, row_data['id'])
                self.table.setItem(row_idx, 0, item_nombre)

                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data['descripcion'])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row_data['estado']))
        except Exception as e:
            logging.error(f"[CRUD_CAJAS] Error cargando datos: {e}")

    def seleccionar_registro(self):
        selected = self.table.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        self.current_caja_id = self.table.item(row, 0).data(Qt.UserRole)
        
        self.le_nombre.setText(self.table.item(row, 0).text())
        self.le_descripcion.setText(self.table.item(row, 1).text())
        self.cb_estado.setCurrentText(self.table.item(row, 2).text())

    def limpiar_form(self):
        self.current_caja_id = None
        self.le_nombre.clear()
        self.le_descripcion.clear()
        self.cb_estado.setCurrentIndex(0)
        self.table.clearSelection()

    def guardar_caja(self):
        cid = self.current_caja_id
        nombre = self.le_nombre.text().strip()
        desc = self.le_descripcion.text().strip()
        estado = self.cb_estado.currentText()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre de la caja es obligatorio.")
            return

        try:
            if cid:
                # Update
                query = "UPDATE configuracion_caja SET nombre=%s, descripcion=%s, estado=%s WHERE id=%s"
                self.db.execute_query(query, (nombre, desc, estado, cid))
                logging.info(f"[CRUD_CAJAS] Actualizando caja ID {cid}: '{nombre}'.")
                QMessageBox.information(self, "Éxito", "Caja actualizada.")
            else:
                # Insert
                query = "INSERT INTO configuracion_caja (nombre, descripcion, estado) VALUES (%s, %s, %s)"
                self.db.execute_query(query, (nombre, desc, estado))
                logging.info(f"[CRUD_CAJAS] Creando nueva caja: '{nombre}'.")
                QMessageBox.information(self, "Éxito", "Nueva caja creada.")
                
            self.limpiar_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_CAJAS] Error guardando caja: {e}")

    def eliminar_caja(self):
        cid = self.current_caja_id
        if not cid:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione una caja de la tabla para eliminar.")
            return

        try:
            query_check = "SELECT COUNT(*) as count FROM movimientos_caja WHERE caja_id = %s"
            result = self.db.execute_query(query_check, (cid,))
            
            if result and result[0]['count'] > 0:
                msg = f"No se puede eliminar la caja ID {cid} porque tiene {result[0]['count']} movimientos asociados."
                QMessageBox.critical(self, "Error de Borrado", msg)
                logging.warning(f"[CRUD_CAJAS] Intento fallido de eliminar caja ID {cid}: Tiene movimientos asociados.")
                return

            confirm = QMessageBox.question(self, "Confirmar Eliminación",
                                           f"¿Está seguro de que desea eliminar la caja ID {cid}?",
                                           QMessageBox.Yes | QMessageBox.No)

            if confirm == QMessageBox.Yes:
                query_delete = "DELETE FROM configuracion_caja WHERE id = %s"
                self.db.execute_query(query_delete, (cid,))
                logging.info(f"[CRUD_CAJAS] Caja ID {cid} eliminada exitosamente.")
                QMessageBox.information(self, "Éxito", "Caja eliminada correctamente.")
                
                self.limpiar_form()
                self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_CAJAS] Error eliminando caja ID {cid}: {e}")
