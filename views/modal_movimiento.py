from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

class ModalMovimiento(QDialog):
    def __init__(self, db_connection, sesion_id, tipo_movimiento, usuario_id, caja_id, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.sesion_id = sesion_id
        self.tipo_movimiento = tipo_movimiento  # 'Ingreso' or 'Egreso'
        self.usuario_id = usuario_id
        self.caja_id = caja_id
        
        self.setWindowTitle(f"Registrar Nuevo {self.tipo_movimiento}")
        self.resize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Categoría
        self.cb_categoria = QComboBox()
        form_layout.addRow("Categoría:", self.cb_categoria)
        
        # Concepto
        self.le_concepto = QLineEdit()
        self.le_concepto.setPlaceholderText("Descripción del gasto/ingreso")
        form_layout.addRow("Concepto:", self.le_concepto)
        
        # Comprobante Tipo y Número
        self.cb_comprobante = QComboBox()
        self.cb_comprobante.addItems(["Factura", "Vale", "Recibo", "Ninguno"])
        form_layout.addRow("Tipo Comprobante:", self.cb_comprobante)
        
        self.le_numero = QLineEdit()
        self.le_numero.setPlaceholderText("Ej. F-001234")
        form_layout.addRow("Nº Comprobante:", self.le_numero)
        
        # Monto
        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(0.01, 999999.99)
        self.sp_monto.setDecimals(2)
        self.sp_monto.setPrefix("$ ")
        form_layout.addRow("Monto:", self.sp_monto)
        
        layout.addLayout(form_layout)
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet("background-color: #0d6efd; color: white; font-weight: bold;")
        self.btn_cancelar = QPushButton("Cancelar")
        
        self.btn_guardar.clicked.connect(self.guardar_movimiento)
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar)
        
        layout.addLayout(btn_layout)

    def load_categories(self):
        query = "SELECT id, nombre FROM categorias_movimiento WHERE tipo = %s AND activo = TRUE"
        categorias = self.db.execute_query(query, (self.tipo_movimiento,))
        
        self.cb_categoria.clear()
        if categorias:
            for cat in categorias:
                # Store the ID in the UserData role of the combo box item
                self.cb_categoria.addItem(cat['nombre'], userData=cat['id'])
        else:
            self.cb_categoria.addItem("Sin categorías")

    def guardar_movimiento(self):
        # Validación básica
        categoria_id = self.cb_categoria.currentData()
        concepto = self.le_concepto.text().strip()
        comp_tipo = self.cb_comprobante.currentText()
        comp_num = self.le_numero.text().strip()
        monto = self.sp_monto.value()
        
        if not categoria_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar una categoría.")
            return
            
        if not concepto:
            QMessageBox.warning(self, "Error", "El concepto no puede estar vacío.")
            return
            
        try:
            query = """
                INSERT INTO movimientos_caja 
                (sesion_id, usuario_id, caja_id, categoria_id, tipo, concepto, comprobante_tipo, comprobante_numero, monto) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                self.sesion_id,
                self.usuario_id,
                self.caja_id,
                categoria_id,
                self.tipo_movimiento,
                concepto,
                comp_tipo if comp_tipo != "Ninguno" else None,
                comp_num if comp_num else None,
                monto
            )
            
            self.db.execute_query(query, params)
            QMessageBox.information(self, "Éxito", f"{self.tipo_movimiento} registrado correctamente.")
            self.accept()  # Cierra la ventana retornando QDialog.Accepted
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", str(e))
