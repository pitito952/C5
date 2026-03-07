from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QWidget, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
import os

class CrudEmpresa(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.setWindowTitle("Configuración de Empresa")
        self.resize(500, 300)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Parámetros del Sistema")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Formulario
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.le_codigo = QLineEdit()
        self.le_codigo.setMaxLength(3)
        self.le_codigo.setPlaceholderText("Ej. EMP")
        
        self.le_nombre = QLineEdit()
        self.le_nombre.setMaxLength(50)
        self.le_nombre.setPlaceholderText("Nombre del Comercio o Empresa")
        
        self.le_logo_path = QLineEdit()
        self.le_logo_path.setReadOnly(True)
        self.btn_browse = QPushButton("Buscar Logo...")
        self.btn_browse.clicked.connect(self.browse_logo)
        
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.le_logo_path)
        logo_layout.addWidget(self.btn_browse)

        self.lbl_logo_preview = QLabel("Sin Logo")
        self.lbl_logo_preview.setAlignment(Qt.AlignCenter)
        self.lbl_logo_preview.setFixedSize(100, 100)
        self.lbl_logo_preview.setStyleSheet("border: 1px solid #ccc;")
        self.lbl_logo_preview.setScaledContents(True)

        form_layout.addRow("Código (3 letras):", self.le_codigo)
        form_layout.addRow("Nombre de Empresa:", self.le_nombre)
        form_layout.addRow("Ruta Logo:", logo_layout)
        form_layout.addRow("", self.lbl_logo_preview)

        layout.addWidget(form_widget)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_cerrar = QPushButton("Cerrar")
        
        self.btn_guardar.clicked.connect(self.guardar_cambios)
        self.btn_cerrar.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cerrar)
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

    def browse_logo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Logo", "", "Imágenes (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.le_logo_path.setText(file_name)
            self.update_preview(file_name)

    def update_preview(self, path):
        if path and os.path.isfile(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.lbl_logo_preview.setPixmap(pixmap.scaled(
                    100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            else:
                self.lbl_logo_preview.setText("Imagen no válida")
        else:
            self.lbl_logo_preview.clear()
            self.lbl_logo_preview.setText("Sin Logo")

    def load_data(self):
        query = "SELECT codigo_empresa, nombre_empresa, ruta_logo FROM parametros_control WHERE id = 1"
        registros = self.db.execute_query(query)
        
        if registros and len(registros) > 0:
            row = registros[0]
            self.le_codigo.setText(row.get('codigo_empresa', ''))
            self.le_nombre.setText(row.get('nombre_empresa', ''))
            
            logo_path = row.get('ruta_logo', '')
            if logo_path:
                self.le_logo_path.setText(logo_path)
                self.update_preview(logo_path)
        else:
            # If no row exists, we might need to create it later, but our init script creates id=1
            pass

    def guardar_cambios(self):
        codigo = self.le_codigo.text().strip().upper()
        nombre = self.le_nombre.text().strip()
        ruta_logo = self.le_logo_path.text().strip()
        
        if not codigo or not nombre:
            QMessageBox.warning(self, "Error", "El Código y el Nombre de la Empresa son obligatorios.")
            return
            
        if len(codigo) > 3:
            QMessageBox.warning(self, "Error", "El Código no puede tener más de 3 letras.")
            return

        # Ensure NULL is sent if empty string for ruta_logo
        logo_val = ruta_logo if ruta_logo else None

        try:
            # Check if record 1 exists
            check = self.db.execute_query("SELECT id FROM parametros_control WHERE id = 1")
            if check:
                query = """
                    UPDATE parametros_control 
                    SET codigo_empresa=%s, nombre_empresa=%s, ruta_logo=%s 
                    WHERE id=1
                """
                self.db.execute_query(query, (codigo, nombre, logo_val))
            else:
                query = """
                    INSERT INTO parametros_control (id, codigo_empresa, nombre_empresa, ruta_logo)
                    VALUES (1, %s, %s, %s)
                """
                self.db.execute_query(query, (codigo, nombre, logo_val))

            QMessageBox.information(self, "Éxito", "Parámetros actualizados correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
