# *****************************************************************************
#
#   Sistema:    C5           -   Módulo de Caja Chica
#   Módulo:     modal_cierre -   Ventana de Cierre de Caja
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   16 |07/03/2026| Antigravity/Addy López |Inicio
# *****************************************************************************
#
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QDoubleSpinBox, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import os
import logging
from decimal import Decimal
from datetime import datetime
from utils.export_pdf import generar_reporte_cierre

class ModalCierre(QDialog):
    def __init__(self, db_connection, sesion_id, simbolo_moneda, caja_nombre, usuario_nombre, parent=None):
        super().__init__(parent)

        self.db = db_connection
        self.sesion_id = sesion_id
        self.simbolo_moneda = simbolo_moneda
        self.caja_nombre = caja_nombre
        self.usuario_nombre = usuario_nombre

        self.lbl_ingresos = self.sp_fisico = self.lbl_inicial = self.lbl_sistema = self.lbl_egresos = None
        self.lbl_sistema = self.lbl_diferencia = self.te_obs = self.btn_cerrar = self.btn_cancelar = None

        self.monto_inicial = 0.0
        self.total_ingresos = 0.0
        self.total_egresos = 0.0
        self.monto_sistema = 0.0
        
        self.setWindowTitle("Arqueo y Cierre de Caja")
        self.resize(450, 450)
        self.setModal(True)
        
        self.setup_ui()
        self.load_session_data()

    def format_money(self, amount):
        """Formatea un monto con el símbolo de moneda configurado."""
        if self.simbolo_moneda:
            return f"{self.simbolo_moneda} {amount:,.2f}"
        else:
            return f"{amount:,.2f}"

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Cierre de Sesión Actual")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(1, 1)

        # Fila 0: Fondo Inicial
        lbl_inicial_tag = QLabel("Fondo Inicial:")
        lbl_inicial_tag.setFont(QFont("Segoe UI", 12))
        self.lbl_inicial = QLabel(self.format_money(0.0))
        self.lbl_inicial.setFont(QFont("Segoe UI", 12))
        self.lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(lbl_inicial_tag, 0, 0)
        grid_layout.addWidget(self.lbl_inicial, 0, 1)
        #self.lbl_inicial.setFont(QFont("Segoe UI", 11))
        #form_layout.addRow("Fondo Inicial:", self.lbl_inicial)

        # Fila 1: Ingresos
        lbl_ingresos_tag = QLabel("Total Ingresos (+):")
        lbl_ingresos_tag.setFont(QFont("Segoe UI", 12))
        self.lbl_ingresos = QLabel(self.format_money(0.0))
        self.lbl_ingresos.setStyleSheet("color: green;")
        self.lbl_ingresos.setFont(QFont("Segoe UI", 12))
        self.lbl_ingresos.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(lbl_ingresos_tag, 1, 0)
        grid_layout.addWidget(self.lbl_ingresos, 1, 1)
        #self.lbl_ingresos.setFont(QFont("Segoe UI", 11))
        #form_layout.addRow("Total Ingresos (+):", self.lbl_ingresos)

        # Fila 2: Egresos
        lbl_egresos_tag = QLabel("Total Egresos (-):")
        lbl_egresos_tag.setFont(QFont("Segoe UI", 12))
        self.lbl_egresos = QLabel(self.format_money(0.0))
        self.lbl_egresos.setStyleSheet("color: red;")
        self.lbl_egresos.setFont(QFont("Segoe UI", 12))
        self.lbl_egresos.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(lbl_egresos_tag, 2, 0)
        grid_layout.addWidget(self.lbl_egresos, 2, 1)
        #self.lbl_egresos.setFont(QFont("Segoe UI", 11))
        #form_layout.addRow("Total Egresos (-):", self.lbl_egresos)

        # Fila 3: Saldo sistema
        lbl_sistema_tag = QLabel("Saldo Según Sistema:")
        lbl_sistema_tag.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_sistema = QLabel(self.format_money(0.0))
        self.lbl_sistema.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_sistema.setStyleSheet("color: blue;")
        self.lbl_sistema.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(lbl_sistema_tag, 3, 0)
        grid_layout.addWidget(self.lbl_sistema, 3, 1)
        #form_layout.addRow("Saldo Según Sistema:", self.lbl_sistema)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        grid_layout.addWidget(line, 4, 0, 1, 2)
        #form_layout.addRow(QLabel("------------------------------------------------------------"), QLabel(""))

        # Linea 5: Dinero Físico
        lbl_fisico_tag = QLabel("Dinero Físico Contado:")
        lbl_fisico_tag.setFont(QFont("Segoe UI", 12))
        self.sp_fisico = QDoubleSpinBox()
        self.sp_fisico.setFont(QFont("Segoe UI", 12))
        self.sp_fisico.setRange(0.00, 999999.99)
        self.sp_fisico.setDecimals(2)
        self.sp_fisico.setPrefix(f"{self.simbolo_moneda} ")
        self.sp_fisico.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sp_fisico.valueChanged.connect(self.calculate_diferencia)
        grid_layout.addWidget(lbl_fisico_tag, 5, 0)
        grid_layout.addWidget(self.sp_fisico, 5, 1)
        #form_layout.addRow("Dinero Físico Contado:", self.sp_fisico)

        # Fila 6: Diferencia
        lbl_diferencia_tag = QLabel("Diferencia:")
        lbl_diferencia_tag.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_diferencia = QLabel(self.format_money(0.0))
        self.lbl_diferencia.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_diferencia.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(lbl_diferencia_tag, 6, 0)
        grid_layout.addWidget(self.lbl_diferencia, 6, 1)
        #self.lbl_diferencia.setFont(QFont("Segoe UI", 13, QFont.Bold))
        #form_layout.addRow("Diferencia:", self.lbl_diferencia)

        # Fila 7: Observaciones
        lbl_obs_tag = QLabel("Observaciones:")
        lbl_obs_tag.setFont(QFont("Segoe UI", 12))
        lbl_obs_tag.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.te_obs = QTextEdit()
        self.te_obs.setFont(QFont("Segoe UI", 11))
        self.te_obs.setPlaceholderText("Obligatorio si hay diferencia...")
        self.te_obs.setMaximumHeight(80)
        grid_layout.addWidget(lbl_obs_tag, 7, 0)
        grid_layout.addWidget(self.te_obs, 7, 1)
        #form_layout.addRow("Observaciones:", self.te_obs)
        
        layout.addLayout(grid_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_cerrar = QPushButton("✔ Confirmar Cierre")
        self.btn_cerrar.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_cerrar.setStyleSheet("background-color: #dc3545; color: white; padding: 8px;")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFont(QFont("Segoe UI", 11))
        
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
            
        self.monto_inicial = Decimal(session_data[0]['monto_inicial'])
        
        query_movs = "SELECT tipo, monto FROM movimientos_caja WHERE sesion_id = %s AND anulado = FALSE"
        movs = self.db.execute_query(query_movs, (self.sesion_id,)) or []
        
        self.total_ingresos = sum(Decimal(m['monto']) for m in movs if m['tipo'] == 'Ingreso')
        self.total_egresos = sum(Decimal(m['monto']) for m in movs if m['tipo'] == 'Egreso')
        
        self.monto_sistema = self.monto_inicial + self.total_ingresos - self.total_egresos
        
        self.lbl_inicial.setText(self.format_money(self.monto_inicial))
        self.lbl_ingresos.setText(self.format_money(self.total_ingresos))
        self.lbl_egresos.setText(self.format_money(self.total_egresos))
        self.lbl_sistema.setText(self.format_money(self.monto_sistema))
        
        self.sp_fisico.setValue(self.monto_sistema)
        self.calculate_diferencia()

    def calculate_diferencia(self):
        diff = self.sp_fisico.value() - self.monto_sistema
        self.lbl_diferencia.setText(self.format_money(diff))
        
        if diff == 0:
            self.lbl_diferencia.setStyleSheet("color: green; font-weight: bold;")
        elif diff > 0:
            self.lbl_diferencia.setStyleSheet("color: blue; font-weight: bold;") # Sobrante
        else:
            self.lbl_diferencia.setStyleSheet("color: red; font-weight: bold;") # Faltante

    def ejecutar_cierre(self):
        fisico = self.sp_fisico.value()
        diff = fisico - self.monto_sistema
        obs = self.te_obs.toPlainText().strip()
        
        if diff != 0 and not obs:
            QMessageBox.warning(self, "Atención", "Como existe una diferencia, las observaciones son obligatorias.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirmar", "¿Está seguro que desea cerrar la caja?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
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
                
                # Generar reporte
                self.generar_y_abrir_reporte(fisico, diff, obs)
                
                QMessageBox.information(self, "Éxito", "Caja cerrada correctamente. Se ha generado el comprobante.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def generar_y_abrir_reporte(self, fisico, diff, obs):
        try:
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            fecha_cierre_str = datetime.now().strftime('%Y-%m-%d')
            caja_nombre_safe = "".join(x for x in self.caja_nombre if x.isalnum() or x in " -_").rstrip()
            filename = f"cierre_sesion_{self.sesion_id}_{fecha_cierre_str}_{caja_nombre_safe}.pdf"
            filepath = os.path.join(reports_dir, filename)

            cierre_data = {
                'fecha_cierre': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'caja_nombre': self.caja_nombre,
                'usuario_nombre': self.usuario_nombre,
                'monto_inicial': self.monto_inicial,
                'total_ingresos': self.total_ingresos,
                'total_egresos': self.total_egresos,
                'saldo_sistema': self.monto_sistema,
                'monto_fisico': fisico,
                'diferencia': diff,
                'observaciones': obs
            }
            
            parametros = {'simbolo_moneda': self.simbolo_moneda}
            
            generar_reporte_cierre(cierre_data, filepath, parametros)
            
            logging.info(f"[MODAL_CIERRE] Reporte de cierre generado en {filepath}")
            os.startfile(filepath)
        except Exception as e:
            logging.error(f"[MODAL_CIERRE] Error al generar o abrir el reporte de cierre: {e}")
            QMessageBox.warning(self, "Error de Reporte", "La caja se cerró, pero no se pudo generar el comprobante en PDF.")
