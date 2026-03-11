from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QWidget, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QPixmap, QRegularExpressionValidator
import os
import logging
from decimal import Decimal, InvalidOperation

class CrudEmpresa(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        logging.info("[CRUD_EMPRESA] Entrando al programa (Configuración de Empresa).")
        self.db = db_connection
        self.setWindowTitle("Configuración de Empresa y Moneda")
        
        if parent:
            self.resize(int(parent.width() * 0.6), int(parent.height() * 0.7))
            self.move(parent.geometry().center() - self.rect().center())
        else:
            self.resize(600, 450)
        
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
        
        # --- Campos de Empresa ---
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

        # --- Campos de Moneda ---
        self.le_simbolo = QLineEdit()
        self.le_simbolo.setMaxLength(5)
        self.le_simbolo.setPlaceholderText("Ej. $ (puede dejarse vacío)")
        
        self.le_nombre_moneda = QLineEdit()
        self.le_nombre_moneda.setMaxLength(50)
        self.le_nombre_moneda.setPlaceholderText("Ej. Peso (puede dejarse vacío)")
        
        self.le_tasa = QLineEdit()
        regex = QRegularExpression(r"^\d{0,7}(\.\d{0,4})?$")
        validator = QRegularExpressionValidator(regex, self.le_tasa)
        self.le_tasa.setValidator(validator)
        self.le_tasa.setPlaceholderText("Ej. 1.0000")

        form_layout.addRow("Código (3 letras):", self.le_codigo)
        form_layout.addRow("Nombre de Empresa:", self.le_nombre)
        form_layout.addRow("Ruta Logo:", logo_layout)
        form_layout.addRow("", self.lbl_logo_preview)
        form_layout.addRow("Símbolo Moneda:", self.le_simbolo)
        form_layout.addRow("Nombre Moneda:", self.le_nombre_moneda)
        form_layout.addRow("Tasa de Cambio:", self.le_tasa)

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
        # Asegurarse de que el registro de parámetros exista
        self.db.execute_query("""
            INSERT IGNORE INTO parametros_control (id, codigo_empresa, nombre_empresa, simbolo_moneda, nombre_moneda, tasa_cambio) 
            VALUES (1, 'EMP', 'Mi Empresa', '$', 'Peso', 1.0000)
        """)
        
        query = "SELECT * FROM parametros_control WHERE id = 1"
        registros = self.db.execute_query(query)
        
        if registros:
            row = registros[0]
            self.le_codigo.setText(row.get('codigo_empresa', ''))
            self.le_nombre.setText(row.get('nombre_empresa', ''))
            self.le_simbolo.setText(row.get('simbolo_moneda', '$'))
            self.le_nombre_moneda.setText(row.get('nombre_moneda', 'Peso'))
            self.le_tasa.setText(str(row.get('tasa_cambio', '1.0000')))
            
            logo_path = row.get('ruta_logo', '')
            if logo_path:
                self.le_logo_path.setText(logo_path)
                self.update_preview(logo_path)
        else:
            logging.error("[CRUD_EMPRESA] No se pudo cargar ni crear el registro de parámetros (id=1).")

    def guardar_cambios(self):
        codigo = self.le_codigo.text().strip().upper()
        nombre = self.le_nombre.text().strip()
        ruta_logo = self.le_logo_path.text().strip()
        simbolo = self.le_simbolo.text().strip()
        nombre_moneda = self.le_nombre_moneda.text().strip()
        tasa_str = self.le_tasa.text().strip()
        
        # Código y Nombre de empresa son los únicos campos de texto obligatorios
        if not all([codigo, nombre, tasa_str]):
            QMessageBox.warning(self, "Error", "Código, Nombre de Empresa y Tasa de Cambio son obligatorios.")
            return
            
        try:
            tasa = Decimal(tasa_str)
        except InvalidOperation:
            QMessageBox.warning(self, "Error", "La Tasa de Cambio debe ser un número válido.")
            return

        logo_val = ruta_logo if ruta_logo else None

        try:
            query = """
                UPDATE parametros_control 
                SET codigo_empresa=%s, nombre_empresa=%s, ruta_logo=%s, 
                    simbolo_moneda=%s, nombre_moneda=%s, tasa_cambio=%s
                WHERE id=1
            """
            params = (codigo, nombre, logo_val, simbolo, nombre_moneda, tasa)
            self.db.execute_query(query, params)

            QMessageBox.information(self, "Éxito", "Parámetros actualizados correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
            logging.error(f"[CRUD_EMPRESA] Error guardando parámetros: {e}")
