# *****************************************************************************
#
#   Sistema:    C5            -   Módulo de Caja Chica
#   Módulo:     report_viewer -   Ventana que muestra el Visor de Reportes.
#                                 Permite visualizar la lista de reportes guar-
#                                 dados en PDF, visualizarlos y reimprimirlos.
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
            self.resize(int(parent.width() * 0.5), int(parent.height() * 0.7))
            self.move(parent.geometry().center() - self.rect().center())
        else:
            self.resize(800, 600)
        
        self.setup_ui()
        self.load_reports()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Reportes de Vales Generados")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        info_text = "Haga doble click en un reporte para abrirlo."
        if self.rol != "Administrador":
            info_text += f" (Mostrando solo reportes de la caja: {self.caja})"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #6c757d; margin-bottom: 10px;")
        layout.addWidget(info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["No. Vale", "Fecha", "Caja", "Nombre de Archivo"])
        for indice, ancho in enumerate((50, 70, 150, 250), start=0):
            self.table.setColumnWidth(indice, ancho)
        #self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
                if filename.lower().startswith("vale_") and filename.lower().endswith(".pdf"):
                    
                    # Filtrar por caja si no es admin
                    if self.rol != "Administrador" and caja_safe not in filename:
                        continue
                    
                    parts = filename.replace(".pdf", "").split("_")
                    if len(parts) >= 4:
                        vale_id = parts[1]
                        fecha_str = parts[2]
                        caja_reporte = parts[3]
                        
                        # Formatear fecha
                        try:
                            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
                            fecha_formateada = fecha_dt.strftime('%d-%m-%Y')
                        except ValueError:
                            fecha_formateada = fecha_str # Mantener original si falla

                        row_position = self.table.rowCount()
                        self.table.insertRow(row_position)
                        
                        self.table.setItem(row_position, 0, QTableWidgetItem(vale_id))
                        self.table.item(row_position, 0).setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_position, 1, QTableWidgetItem(fecha_formateada))
                        self.table.item(row_position, 1).setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_position, 2, QTableWidgetItem(caja_reporte))
                        self.table.setItem(row_position, 3, QTableWidgetItem(filename))
            
            self.table.sortByColumn(1, Qt.DescendingOrder) # Ordenar por fecha
            
        except Exception as e:
            logging.error(f"[REPORT_VIEWER] Error al cargar la lista de reportes: {e}")
            QMessageBox.critical(self, "Error", "No se pudo cargar la lista de reportes.")

    def abrir_reporte(self, item):
        if not item: return
        
        row = item.row()
        filename_item = self.table.item(row, 3)
        
        if filename_item:
            filepath = os.path.join(self.reports_dir, filename_item.text())
            if os.path.exists(filepath):
                try:
                    logging.info(f"[REPORT_VIEWER] Abriendo reporte: {filepath}")
                    os.startfile(filepath)
                except Exception as e:
                    logging.error(f"[REPORT_VIEWER] No se pudo abrir el archivo '{filepath}': {e}")
                    QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo.\n{e}")
            else:
                QMessageBox.warning(self, "Archivo no encontrado", "El archivo del reporte ya no existe en el directorio.")
                self.load_reports() # Recargar lista por si se borró
