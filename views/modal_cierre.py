from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ModalCierre(QDialog):
    def __init__(self, db_connection, sesion_id, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.sesion_id = sesion_id
        
        self.monto_sistema = 0.0
        
        self.setWindowTitle("Arqueo y Cierre de Caja")
        self.resize(450, 450)
        self.setModal(True)
        
        self.setup_ui()
        self.load_session_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Cierre de Sesión Actual")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        self.lbl_inicial = QLabel("$ 0.00")
        form_layout.addRow("Fondo Inicial:", self.lbl_inicial)
        
        self.lbl_ingresos = QLabel("$ 0.00")
        self.lbl_ingresos.setStyleSheet("color: green;")
        form_layout.addRow("Total Ingresos (+):", self.lbl_ingresos)
        
        self.lbl_egresos = QLabel("$ 0.00")
        self.lbl_egresos.setStyleSheet("color: red;")
        form_layout.addRow("Total Egresos (-):", self.lbl_egresos)
        
        self.lbl_sistema = QLabel("$ 0.00")
        self.lbl_sistema.setFont(QFont("Arial", 12, QFont.Bold))
        self.lbl_sistema.setStyleSheet("color: blue;")
        form_layout.addRow("Saldo Según Sistema:", self.lbl_sistema)
        
        # Separator
        form_layout.addRow(QLabel("--------------------------------------------------"), QLabel(""))
        
        self.sp_fisico = QDoubleSpinBox()
        self.sp_fisico.setRange(0.00, 999999.99)
        self.sp_fisico.setDecimals(2)
        self.sp_fisico.setPrefix("$ ")
        self.sp_fisico.valueChanged.connect(self.calculate_diferencia)
        form_layout.addRow("Dinero Físico Contado:", self.sp_fisico)
        
        self.lbl_diferencia = QLabel("$ 0.00")
        self.lbl_diferencia.setFont(QFont("Arial", 12, QFont.Bold))
        form_layout.addRow("Diferencia:", self.lbl_diferencia)
        
        self.te_obs = QTextEdit()
        self.te_obs.setPlaceholderText("Observaciones (Ej. Faltante por vuelto mal dado)")
        self.te_obs.setMaximumHeight(80)
        form_layout.addRow("Observaciones:", self.te_obs)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_cerrar = QPushButton("✔ Confirmar Cierre")
        self.btn_cerrar.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; height: 30px;")
        self.btn_cancelar = QPushButton("Cancelar")
        
        self.btn_cerrar.clicked.connect(self.ejecutar_cierre)
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_cerrar)
        
        layout.addLayout(btn_layout)

    def load_session_data(self):
        query_session = "SELECT monto_inicial FROM sesiones_caja WHERE id = %s"
        session_data = self.db.execute_query(query_session, (self.sesion_id,))
        if not session_data:
            return
            
        monto_inicial = float(session_data[0]['monto_inicial'])
        
        query_movs = "SELECT tipo, monto FROM movimientos_caja WHERE sesion_id = %s AND anulado = FALSE"
        movs = self.db.execute_query(query_movs, (self.sesion_id,)) or []
        
        total_in = sum(float(m['monto']) for m in movs if m['tipo'] == 'Ingreso')
        total_out = sum(float(m['monto']) for m in movs if m['tipo'] == 'Egreso')
        
        self.monto_sistema = monto_inicial + total_in - total_out
        
        self.lbl_inicial.setText(f"$ {monto_inicial:.2f}")
        self.lbl_ingresos.setText(f"$ {total_in:.2f}")
        self.lbl_egresos.setText(f"$ {total_out:.2f}")
        self.lbl_sistema.setText(f"$ {self.monto_sistema:.2f}")
        
        # Prepopulate physical cash to equal internal logic
        self.sp_fisico.setValue(self.monto_sistema)
        self.calculate_diferencia()

    def calculate_diferencia(self):
        diff = self.sp_fisico.value() - self.monto_sistema
        self.lbl_diferencia.setText(f"$ {diff:.2f}")
        
        if diff == 0:
            self.lbl_diferencia.setStyleSheet("color: green;")
        elif diff > 0:
            self.lbl_diferencia.setStyleSheet("color: blue;") # Sobrante
        else:
            self.lbl_diferencia.setStyleSheet("color: red;") # Faltante

    def ejecutar_cierre(self):
        fisico = self.sp_fisico.value()
        diff = fisico - self.monto_sistema
        obs = self.te_obs.toPlainText().strip()
        
        if diff != 0 and not obs:
            QMessageBox.warning(self, "Atención", "Como existe una diferencia, las observaciones son obligatorias.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirmar", "¿Está seguro que desea cerrar la caja?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                query = """
                    UPDATE sesiones_caja 
                    SET estado = 'Cerrada', fecha_cierre = NOW(), 
                        monto_final_sistema = %s, monto_final_fisico = %s,
                        diferencia = %s, observaciones_cierre = %s
                    WHERE id = %s
                """
                params = (self.monto_sistema, fisico, diff, obs, self.sesion_id)
                self.db.execute_query(query, params)
                QMessageBox.information(self, "Éxito", "Caja cerrada correctamente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
