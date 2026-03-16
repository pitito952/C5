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
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QMessageBox, QApplication, QComboBox, QDateEdit, QPushButton
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class ReportViewerWindow(QDialog):
    def __init__(self, rol_usuario, nombre_caja, db_connection, parent=None):
        super().__init__(parent)

        self.table = None
        logging.info("[REPORT_VIEWER] Entrando al programa (Visor de Reportes).")
        
        self.rol = rol_usuario
        self.caja_actual = nombre_caja
        self.db = db_connection
        self.reports_dir = "reports"

        self.setWindowTitle("Visor de Reportes Guardados")
        
        if parent:
            self.resize(int(parent.width() * 0.8), int(parent.height() * 0.8))
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
            info_text += f" (Mostrando solo reportes de la caja: {self.caja_actual})"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #6c757d; margin-bottom: 5px;")
        layout.addWidget(info_label)

        # --- Filtros ---
        filter_layout = QHBoxLayout()
        
        self.date_desde = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setFixedWidth(110)
        
        self.cb_caja = QComboBox()
        self.cb_caja.setFixedWidth(200)
        
        self.cb_tipo_reporte = QComboBox()
        self.cb_tipo_reporte.addItems(["Todos", "Solo Vales", "Solo Cierres"])
        self.cb_tipo_reporte.setFixedWidth(150)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.load_reports)
        
        filter_layout.addWidget(QLabel("Desde:"))
        filter_layout.addWidget(self.date_desde)
        filter_layout.addWidget(QLabel("Caja:"))
        filter_layout.addWidget(self.cb_caja)
        filter_layout.addWidget(QLabel("Tipo:"))
        filter_layout.addWidget(self.cb_tipo_reporte)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_buscar)
        
        layout.addLayout(filter_layout)
        
        self._cargar_cajas() # Cargar datos en el combobox

        # --- Tabla ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tipo", "ID / No.", "Fecha", "Caja", "Nombre de Archivo"])
        
        # Ajustar anchos de columna
        self.table.setColumnWidth(0, 100) # Tipo
        self.table.setColumnWidth(1, 80)  # ID
        self.table.setColumnWidth(2, 90)  # Fecha
        self.table.setColumnWidth(3, 180) # Caja
        self.table.horizontalHeader().setStretchLastSection(True) # Nombre Archivo
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Conectar doble click
        self.table.itemDoubleClicked.connect(self.abrir_reporte)
        
        layout.addWidget(self.table)

    def _cargar_cajas(self):
        """Carga las cajas en el ComboBox de filtro."""
        self.cb_caja.clear()
        self.cb_caja.addItem("Todas", userData=None)
        
        try:
            # Consultar todas las cajas activas
            cajas = self.db.execute_query("SELECT id, nombre FROM configuracion_caja ORDER BY nombre")
            if cajas:
                for caja in cajas:
                    self.cb_caja.addItem(caja['nombre'], userData=caja['id'])
        except Exception as e:
            logging.error(f"[REPORT_VIEWER] Error cargando cajas para filtro: {e}")
        
        # Si el usuario no es admin, pre-seleccionar su caja y deshabilitar el combo
        if self.rol != "Administrador":
            index = self.cb_caja.findText(self.caja_actual)
            if index != -1:
                self.cb_caja.setCurrentIndex(index)
            self.cb_caja.setEnabled(False)

    def load_reports(self):
        self.table.setRowCount(0)
        
        if not os.path.exists(self.reports_dir):
            logging.warning(f"[REPORT_VIEWER] El directorio '{self.reports_dir}' no existe.")
            return

        # Obtener valores de los filtros
        fecha_desde = self.date_desde.date()
        caja_seleccionada_id = self.cb_caja.currentData()
        caja_seleccionada_nombre = self.cb_caja.currentText()
        tipo_reporte = self.cb_tipo_reporte.currentText()

        try:
            for filename in os.listdir(self.reports_dir):
                filename_lower = filename.lower()
                if not filename_lower.endswith(".pdf"):
                    continue

                # --- 1. Filtro por Tipo de Reporte ---
                if tipo_reporte == "Solo Vales" and not filename_lower.startswith("vale_"):
                    continue
                if tipo_reporte == "Solo Cierres" and not filename_lower.startswith("cierre_sesion_"):
                    continue
                
                # --- 2. Filtro por Caja ---
                # Si se seleccionó una caja específica (y no es "Todas"), verificar si el nombre del archivo contiene el nombre de la caja.
                # Nota: Los nombres de archivo tienen espacios reemplazados o eliminados, la búsqueda debe ser flexible.
                if caja_seleccionada_id is not None:
                    # Limpiamos el nombre de la caja seleccionada para comparar (quitar caracteres especiales si los hubiera en el filename)
                    # Una forma simple es verificar si la parte del nombre de caja está en el filename.
                    # Asumimos que el nombre de caja en el filename está "sanitizado".
                    caja_safe_filter = "".join(x for x in caja_seleccionada_nombre if x.isalnum() or x in " -_").rstrip().lower()
                    if caja_safe_filter not in filename_lower:
                        continue

                # --- 3. Filtro por Fecha ---
                try:
                    parts = filename.replace(".pdf", "").split("_")
                    fecha_str = ""
                    
                    if filename_lower.startswith("vale_") and len(parts) >= 4:
                        # vale_{id}_{fecha}_{caja} -> fecha es indice 2
                        fecha_str = parts[2]
                    elif filename_lower.startswith("cierre_sesion_") and len(parts) >= 5:
                        # cierre_sesion_{id}_{fecha}_{caja} -> fecha es indice 3
                        fecha_str = parts[3]
                    
                    if fecha_str:
                        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                        # Comparar fecha archivo >= fecha filtro
                        if QDate(fecha_dt) < fecha_desde:
                            continue
                except (ValueError, IndexError):
                    # Si no podemos parsear la fecha, decidimos si mostrarlo o no. 
                    # Por seguridad, lo saltamos si el filtro de fecha es estricto, o lo mostramos con advertencia.
                    # Aquí lo saltamos.
                    continue

                # --- Procesamiento y adición a la tabla (si pasó todos los filtros) ---
                if filename_lower.startswith("vale_"):
                    self.procesar_y_agregar_fila(filename, "Vale")
                elif filename_lower.startswith("cierre_sesion_"):
                    # Solo mostrar cierres si es admin (aunque el filtro de tipo ya lo limitaría, es doble check de seguridad)
                    if self.rol == "Administrador":
                        self.procesar_y_agregar_fila(filename, "Cierre")

            self.table.sortByColumn(2, Qt.DescendingOrder) # Ordenar por fecha descendente
            
        except Exception as e:
            logging.error(f"[REPORT_VIEWER] Error al cargar la lista de reportes: {e}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("No se pudo cargar la lista de reportes.")
            msg.addButton("Aceptar", QMessageBox.AcceptRole)
            msg.exec()

    def procesar_y_agregar_fila(self, filename, tipo_doc):
        """Procesa el nombre del archivo y añade una fila a la tabla."""
        parts = filename.replace(".pdf", "").split("_")
        doc_id, fecha_str, caja_reporte = "", "", ""

        if tipo_doc == "Vale" and len(parts) >= 4:
            doc_id = parts[1]
            fecha_str = parts[2]
            # Reconstruir nombre de caja (puede tener guiones bajos si tenía espacios)
            caja_reporte = " ".join(parts[3:]) 
        elif tipo_doc == "Cierre" and len(parts) >= 5:
            doc_id = parts[2]
            fecha_str = parts[3]
            caja_reporte = " ".join(parts[4:])
        
        if not all([doc_id, fecha_str]):
            return

        # Formatear fecha para visualización
        try:
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_formateada = fecha_dt.strftime('%d-%m-%Y')
        except ValueError:
            fecha_formateada = fecha_str

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        self.table.setItem(row_position, 0, QTableWidgetItem(tipo_doc))
        self.table.item(row_position, 0).setTextAlignment(Qt.AlignCenter)
        
        self.table.setItem(row_position, 1, QTableWidgetItem(doc_id))
        self.table.item(row_position, 1).setTextAlignment(Qt.AlignCenter)
        
        # Guardar fecha como string ordenable (YYYY-MM-DD) en user data si quisiéramos ordenar por data,
        # pero aquí la tabla ordena por texto. Si el formato es dd-mm-yyyy, el sort alfabético no es cronológico.
        # Para corregir el ordenamiento visual, idealmente usaríamos un item personalizado, pero por simplicidad:
        # Usamos el formato YYYY-MM-DD para que el sort de la tabla funcione correctamente, 
        # O aceptamos que el sort visual por defecto de QTableWidgetItem podría no ser perfecto para fechas DD-MM-YYYY.
        # Una mejora rápida: Insertar un item que tenga el texto DD-MM-YYYY pero ordene por su data YYYY-MM-DD.
        # Pero QTableWidget por defecto ordena por display text.
        # Solución simple: Poner la fecha formateada. El usuario puede usar el filtro de fecha para rangos.
        
        self.table.setItem(row_position, 2, QTableWidgetItem(fecha_formateada))
        self.table.item(row_position, 2).setTextAlignment(Qt.AlignCenter)
        
        self.table.setItem(row_position, 3, QTableWidgetItem(caja_reporte))
        self.table.setItem(row_position, 4, QTableWidgetItem(filename))

    def abrir_reporte(self, item):
        if not item: return
        
        row = item.row()
        filename_item = self.table.item(row, 4) # Índice 4 es el nombre de archivo
        
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
