from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from utils.export_pdf import generar_listado_pdf
import os

class ModalReporte(QDialog):
    def __init__(self, db_connection, user_data, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.user_data = user_data  # Should contain 'id', 'username', 'rol'
        
        self.setWindowTitle("Generar Reporte de Movimientos")
        self.resize(350, 200)
        self.setModal(True)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Criterios del Reporte (PDF)")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        # Default to first day of current month
        self.date_desde.setDate(QDate.currentDate().addDays(-QDate.currentDate().day() + 1))
        form_layout.addRow("Desde:", self.date_desde)
        
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        form_layout.addRow("Hasta:", self.date_hasta)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_generar = QPushButton("Generar PDF")
        self.btn_generar.setStyleSheet("background-color: #198754; color: white; font-weight: bold;")
        self.btn_cancelar = QPushButton("Cancelar")
        
        self.btn_generar.clicked.connect(self.ejecutar_reporte)
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_generar)
        
        layout.addLayout(btn_layout)

    def ejecutar_reporte(self):
        fecha_ini = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_fin = self.date_hasta.date().toString("yyyy-MM-dd")
        
        # Validar lógica de fechas
        if self.date_desde.date() > self.date_hasta.date():
            QMessageBox.warning(self, "Error", "La fecha 'Desde' no puede ser mayor a 'Hasta'.")
            return
            
        # Fetch movements between these dates (only active ones)
        # Filtered by the current logged user assuming the prompt means "his/her" movements or general?
        # A cajero only reports their own, an Admin can see all? 
        # For simplicity, we filter by the user passing the query.
        
        if self.user_data['rol'] == 'Administrador':
            query = """
                SELECT m.fecha_hora, m.tipo, c.nombre as categoria, 
                       cfg.nombre as caja, u.username as usuario, 
                       m.concepto, m.monto
                FROM movimientos_caja m
                JOIN categorias_movimiento c ON m.categoria_id = c.id
                JOIN sesiones_caja s ON m.sesion_id = s.id
                JOIN configuracion_caja cfg ON m.caja_id = cfg.id
                JOIN usuarios u ON m.usuario_id = u.id
                WHERE DATE(m.fecha_hora) BETWEEN %s AND %s AND m.anulado = FALSE
                ORDER BY m.fecha_hora ASC
            """
            params = (fecha_ini, fecha_fin)
        else:
            query = """
                SELECT m.fecha_hora, m.tipo, c.nombre as categoria, 
                       cfg.nombre as caja, u.username as usuario, 
                       m.concepto, m.monto
                FROM movimientos_caja m
                JOIN categorias_movimiento c ON m.categoria_id = c.id
                JOIN sesiones_caja s ON m.sesion_id = s.id
                JOIN configuracion_caja cfg ON m.caja_id = cfg.id
                JOIN usuarios u ON m.usuario_id = u.id
                WHERE DATE(m.fecha_hora) BETWEEN %s AND %s AND m.anulado = FALSE AND s.usuario_id = %s
                ORDER BY m.fecha_hora ASC
            """
            params = (fecha_ini, fecha_fin, self.user_data['id'])
            
        movimientos = self.db.execute_query(query, params)
        
        if not movimientos:
            QMessageBox.information(self, "Sin Resultados", "No hay movimientos registrados en este rango de fechas.")
            return
            
        # Call FPDF generator
        info_extra = {
            "desde": self.date_desde.date().toString("dd/MM/yyyy"),
            "hasta": self.date_hasta.date().toString("dd/MM/yyyy"),
            "usuario": self.user_data['username']
        }
        
        try:
            # Let's save the file on the user's current directory or desktop?
            # We will save it in the app dir for now.
            pdf_path = os.path.join(os.getcwd(), f"reporte_{fecha_ini}_a_{fecha_fin}.pdf")
            
            parametros = {}
            try:
                p_res = self.db.execute_query("SELECT * FROM parametros_control WHERE id = 1")
                if p_res:
                    parametros = p_res[0]
            except Exception:
                pass
                
            generar_listado_pdf(movimientos, info_extra, parametros, pdf_path)
            
            QMessageBox.information(self, "Éxito", f"Reporte generado exitosamente:\n{pdf_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Generando PDF", str(e))
