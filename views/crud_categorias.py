from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox, QHeaderView, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

class CrudCategorias(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        logging.info("[CRUD_CATEGORIAS] Entrando al programa (Gestión de Categorías).")
        self.db = db_connection
        self.setWindowTitle("Gestión de Categorías")
        self.resize(600, 400)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Administración de Categorías de Movimiento")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Formulario
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.le_id = QLineEdit()
        self.le_id.setReadOnly(True)
        self.le_id.setPlaceholderText("ID Auto")
        
        self.le_nombre = QLineEdit()
        
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Ingreso", "Egreso"])

        form_layout.addRow("ID:", self.le_id)
        form_layout.addRow("Nombre Categoria:", self.le_nombre)
        form_layout.addRow("Tipo:", self.cb_tipo)
        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar / Actualizar")
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet("background-color: #dc3545; color: white;")

        self.btn_guardar.clicked.connect(self.guardar_categoria)
        self.btn_limpiar.clicked.connect(self.limpiar_form)
        self.btn_eliminar.clicked.connect(self.eliminar_categoria)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Tipo Global"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.seleccionar_registro)
        layout.addWidget(self.table)

    def load_data(self):
        try:
            query = "SELECT id, nombre, tipo FROM categorias_movimiento ORDER BY tipo, nombre"
            registros = self.db.execute_query(query) or []
            
            self.table.setRowCount(len(registros))
            for row_idx, row_data in enumerate(registros):
                items = [
                    str(row_data['id']),
                    row_data['nombre'],
                    row_data['tipo']
                ]
                for col_idx, val in enumerate(items):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(val))
        except Exception as e:
            logging.error(f"[CRUD_CATEGORIAS] Error cargando datos: {e}")

    def seleccionar_registro(self):
        selected = self.table.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        self.le_id.setText(self.table.item(row, 0).text())
        self.le_nombre.setText(self.table.item(row, 1).text())
        self.cb_tipo.setCurrentText(self.table.item(row, 2).text())

    def limpiar_form(self):
        self.le_id.clear()
        self.le_nombre.clear()
        self.cb_tipo.setCurrentIndex(0)
        self.table.clearSelection()

    def guardar_categoria(self):
        cid = self.le_id.text().strip()
        nombre = self.le_nombre.text().strip()
        tipo = self.cb_tipo.currentText()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "Debe escribir un nombre para la categoría.")
            return

        try:
            if cid:
                # Update
                query = "UPDATE categorias_movimiento SET nombre=%s, tipo=%s WHERE id=%s"
                self.db.execute_query(query, (nombre, tipo, cid))
                logging.info(f"[CRUD_CATEGORIAS] Actualizando categoría ID {cid}: '{nombre}'.")
                QMessageBox.information(self, "Éxito", "Categoría actualizada.")
            else:
                # Insert
                query = "INSERT INTO categorias_movimiento (nombre, tipo) VALUES (%s, %s)"
                self.db.execute_query(query, (nombre, tipo))
                logging.info(f"[CRUD_CATEGORIAS] Creando nueva categoría: '{nombre}'.")
                QMessageBox.information(self, "Éxito", "Categoría creada.")
                
            self.limpiar_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_CATEGORIAS] Error guardando categoría: {e}")

    def eliminar_categoria(self):
        cid = self.le_id.text().strip()
        if not cid:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione una categoría de la tabla para eliminar.")
            return

        try:
            # Verificar si la categoría está en uso
            query_check = "SELECT COUNT(*) as count FROM movimientos_caja WHERE categoria_id = %s"
            result = self.db.execute_query(query_check, (cid,))
            
            if result and result[0]['count'] > 0:
                msg = f"No se puede eliminar la categoría ID {cid} porque tiene {result[0]['count']} movimientos asociados."
                QMessageBox.critical(self, "Error de Borrado", msg)
                logging.warning(f"[CRUD_CATEGORIAS] Intento fallido de eliminar categoría ID {cid}: Tiene movimientos asociados.")
                return

            # Pedir confirmación
            confirm = QMessageBox.question(self, "Confirmar Eliminación",
                                           f"¿Está seguro de que desea eliminar la categoría ID {cid}?",
                                           QMessageBox.Yes | QMessageBox.No)

            if confirm == QMessageBox.Yes:
                # Eliminar
                query_delete = "DELETE FROM categorias_movimiento WHERE id = %s"
                self.db.execute_query(query_delete, (cid,))
                logging.info(f"[CRUD_CATEGORIAS] Categoría ID {cid} eliminada exitosamente.")
                QMessageBox.information(self, "Éxito", "Categoría eliminada correctamente.")
                
                self.limpiar_form()
                self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_CATEGORIAS] Error eliminando categoría ID {cid}: {e}")
