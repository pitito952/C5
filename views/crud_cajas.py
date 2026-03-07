from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox, QHeaderView, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class CrudCajas(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.setWindowTitle("Gestión de Cajas")
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
        
        self.le_id = QLineEdit()
        self.le_id.setReadOnly(True)
        self.le_id.setPlaceholderText("ID Auto")
        
        self.le_nombre = QLineEdit()
        self.le_descripcion = QLineEdit()
        
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Activa", "Inactiva"])

        form_layout.addRow("ID:", self.le_id)
        form_layout.addRow("Nombre Caja:", self.le_nombre)
        form_layout.addRow("Descripción:", self.le_descripcion)
        form_layout.addRow("Estado:", self.cb_estado)
        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar / Actualizar")
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        
        self.btn_guardar.clicked.connect(self.guardar_caja)
        self.btn_limpiar.clicked.connect(self.limpiar_form)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.seleccionar_registro)
        layout.addWidget(self.table)

    def load_data(self):
        query = "SELECT id, nombre, descripcion, estado FROM configuracion_caja ORDER BY id"
        registros = self.db.execute_query(query) or []
        
        self.table.setRowCount(len(registros))
        for row_idx, row_data in enumerate(registros):
            items = [
                str(row_data['id']),
                row_data['nombre'],
                str(row_data['descripcion']),
                row_data['estado']
            ]
            for col_idx, val in enumerate(items):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def seleccionar_registro(self):
        selected = self.table.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        self.le_id.setText(self.table.item(row, 0).text())
        self.le_nombre.setText(self.table.item(row, 1).text())
        self.le_descripcion.setText(self.table.item(row, 2).text())
        self.cb_estado.setCurrentText(self.table.item(row, 3).text())

    def limpiar_form(self):
        self.le_id.clear()
        self.le_nombre.clear()
        self.le_descripcion.clear()
        self.cb_estado.setCurrentIndex(0)
        self.table.clearSelection()

    def guardar_caja(self):
        cid = self.le_id.text().strip()
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
                QMessageBox.information(self, "Éxito", "Caja actualizada.")
            else:
                # Insert
                query = "INSERT INTO configuracion_caja (nombre, descripcion, estado) VALUES (%s, %s, %s)"
                self.db.execute_query(query, (nombre, desc, estado))
                QMessageBox.information(self, "Éxito", "Nueva caja creada.")
                
            self.limpiar_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
