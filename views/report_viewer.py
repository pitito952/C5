# *****************************************************************************
#
#   Sistema:    C5            -   Módulo de Caja Chica
#   Módulo:     report_viewer -   Ventana que muestra el Visor de Reportes.
#                                 Permite visualizar la lista de reportes guar-
#                                 dados en PDF para efectos de impresión.
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   ...
#   13 |07/03/2026| Antigravity/Addy López |Cambio de formato de fecha.
# *****************************************************************************
#
import os
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ReportViewerWindow(QDialog):
    def __init__(self, rol_usuario, nombre_caja, parent=None):
        super().__init__(parent)

        self.table = None
        logging.info("[REPORT_VIEWER] Entrando al programa (Visor de Reportes).")
        
        self.rol = rol_usuario
        self.caja = nombre_caja
        self.reports_dir = "reports"

        self.setWindowTitle("Visor de Reportes Guardados")
        
        if parent:
            self.resize(int(parent.width() * 0.7), int(parent.height() * 0.7))
            self.move(parent.geometry().center() - self.rect().center())
        else:
            self.resize(900, 600)
        
        self.setup_ui()
        self.load_reports()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title_text = "Reportes de Vales y Cierres" if self.rol == "Administrador" else "Reportes de Vales Generados"
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        info_text = "Haga doble click en un reporte para abrirlo."
        if self.rol != "Administrador":
            info_text += f" (Mostrando solo reportes de la caja: {self.caja})"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #6c757d; margin-bottom: 10px;")
        layout.addWidget(info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5) # Aumentado a 5 columnas
        self.table.setHorizontalHeaderLabels(["Tipo", "ID / No.", "Fecha", "Caja", "Nombre de Archivo"])
        
        # Ajustar anchos de columna
        self.table.setColumnWidth(0, 100) # Tipo
        self.table.setColumnWidth(1, 80)  # ID
        self.table.setColumnWidth(2, 90)  # Fecha
        self.table.setColumnWidth(3, 180) # Caja
        self.table.setColumnWidth(4, 250) # Nombre Archivo (el resto se ajusta o scroll)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Conectar doble click
        self.table.itemDoubleClicked.connect(self.abrir_reporte)
        
        layout.addWidget(self.table)

    def load_reports(self):
        self.table.setRowCount(0)
        
        if not os.path.exists(self.reports_dir):
            logging.warning(f"[REPORT_VIEWER] El directorio '{self.reports_dir}' no existe.")
            return

        try:
            caja_safe = "".join(x for x in self.caja if x.isalnum() or x in " -_").rstrip()
            
            for filename in os.listdir(self.reports_dir):
                filename_lower = filename.lower()
                
                if not filename_lower.endswith(".pdf"):
                    continue

                # --- PROCESAR VALES ---
                if filename_lower.startswith("vale_"):
                    # Filtrar por caja si no es admin
                    if self.rol != "Administrador" and caja_safe not in filename:
                        continue
                    
                    parts = filename.replace(".pdf", "").split("_")
                    if len(parts) >= 4:
                        tipo_doc = "Vale"
                        doc_id = parts[1]
                        fecha_str = parts[2]
                        caja_reporte = parts[3]
                        self.agregar_fila(tipo_doc, doc_id, fecha_str, caja_reporte, filename)

                # --- PROCESAR CIERRES DE SESIÓN (Solo Admin) ---
                elif filename_lower.startswith("cierre_sesion_"):
                    if self.rol == "Administrador":
                        parts = filename.replace(".pdf", "").split("_")
                        # Formato esperado: cierre_sesion_{id}_{fecha}_{caja}.pdf
                        # parts[0]="cierre", parts[1]="sesion", parts[2]=id, parts[3]=fecha, parts[4...]=caja
                        if len(parts) >= 5:
                            tipo_doc = "Cierre"
                            doc_id = parts[2]
                            fecha_str = parts[3]
                            # Reconstruir nombre de caja si tenía guiones bajos
                            caja_reporte = "_".join(parts[4:]) 
                            self.agregar_fila(tipo_doc, doc_id, fecha_str, caja_reporte, filename)

            self.table.sortByColumn(2, Qt.DescendingOrder) # Ordenar por fecha
            
        except Exception as e:
            logging.error(f"[REPORT_VIEWER] Error al cargar la lista de reportes: {e}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("No se pudo cargar la lista de reportes.")
            msg.addButton("Aceptar", QMessageBox.AcceptRole)
            msg.exec()

    def agregar_fila(self, tipo, doc_id, fecha_str, caja, filename):
        # Formatear fecha
        try:
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_formateada = fecha_dt.strftime('%d-%m-%Y') # Formato tabla
            fecha_sortable = fecha_str # Usar formato YYYY-MM-DD para ordenamiento si fuera necesario, pero visualmente mostramos dd-mm-yyyy
        except ValueError:
            fecha_formateada = fecha_str

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        self.table.setItem(row_position, 0, QTableWidgetItem(tipo))
        self.table.item(row_position, 0).setTextAlignment(Qt.AlignCenter)
        
        self.table.setItem(row_position, 1, QTableWidgetItem(doc_id))
        self.table.item(row_position, 1).setTextAlignment(Qt.AlignCenter)
        
        # Usamos la fecha formateada para visualización
        item_fecha = QTableWidgetItem(fecha_formateada)
        item_fecha.setData(Qt.UserRole, fecha_str) # Guardar fecha sin formato para ordenamiento potencial
        self.table.setItem(row_position, 2, item_fecha)
        self.table.item(row_position, 2).setTextAlignment(Qt.AlignCenter)
        
        self.table.setItem(row_position, 3, QTableWidgetItem(caja))
        self.table.setItem(row_position, 4, QTableWidgetItem(filename))

    def abrir_reporte(self, item):
        if not item: return
        
        row = item.row()
        filename_item = self.table.item(row, 4) # Índice 4 es el nombre de archivo ahora
        
        if filename_item:
            filepath = os.path.join(self.reports_dir, filename_item.text())
            if os.path.exists(filepath):
                try:
                    logging.info(f"[REPORT_VIEWER] Abriendo reporte: {filepath}")
                    os.startfile(filepath)
                except Exception as e:
                    logging.error(f"[REPORT_VIEWER] No se pudo abrir el archivo '{filepath}': {e}")
                    
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Error")
                    msg.setText(f"No se pudo abrir el archivo.\n{e}")
                    msg.addButton("Aceptar", QMessageBox.AcceptRole)
                    msg.exec()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Archivo no encontrado")
                msg.setText("El archivo del reporte ya no existe en el directorio.")
                msg.addButton("Aceptar", QMessageBox.AcceptRole)
                msg.exec()

                self.load_reports() # Recargar lista por si se borró
