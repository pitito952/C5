# *****************************************************************************
#
#   Sistema:    C5          -   Módulo de Caja Chica
#   Módulo:     main_window -   Ventana Principal de la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   02 |07/03/2026| Antigravity/Addy López |Implementación de Sistema de Logs.
#   03 |07/03/2026| Antigravity/Addy López |Corrección de generación de reportes PDF.
#   04 |07/03/2026| Antigravity/Addy López |Alineación con esquema de BD (Sesiones).
#   05 |07/03/2026| Antigravity/Addy López |Restauración de Dashboard y mejoras de UI.
# *****************************************************************************
#
import logging
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QDateEdit, QFileDialog, QMessageBox, QDialog, QFormLayout, QFrame, QMenu
)
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QFont, QAction, QRegularExpressionValidator, QColor
from database.connection import DatabaseConnection
from views.crud_cajas import CrudCajas
from views.crud_categorias import CrudCategorias
from views.crud_usuarios import CrudUsuarios
from utils.export_pdf import generar_listado_pdf, generar_vale_pdf

class MainWindow(QMainWindow):
    def __init__(self, usuario_id, username, rol, caja_id, caja_nombre):
        super().__init__()
        logging.info("[MAIN_WINDOW] Entrando al programa (Ventana Principal).")

        self.usuario_id = usuario_id
        self.username = username
        self.rol = rol
        self.caja_id = caja_id
        self.caja_nombre = caja_nombre
        self.sesion_id = None # ID de la sesión activa
        
        self.db = DatabaseConnection()
        
        self.setWindowTitle("C5 - Módulo de Caja Chica")
        self.resize(1100, 800)
        
        self.setup_ui()
        self.inicializar_sesion()
        self.load_initial_data()

    def setup_ui(self):
        # --- Menu Bar ---
        menu_bar = self.menuBar()
        
        # Menu Archivo
        file_menu = menu_bar.addMenu("Archivo")
        
        report_action = QAction("Generar Reporte General", self)
        report_action.triggered.connect(self.mostrar_dialogo_reporte)
        file_menu.addAction(report_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Administración (solo para Admins)
        if self.rol == "Administrador":
            admin_menu = menu_bar.addMenu("Administración")
            
            users_action = QAction("Gestionar Usuarios", self)
            users_action.triggered.connect(self.abrir_crud_usuarios)
            admin_menu.addAction(users_action)
            
            cajas_action = QAction("Gestionar Cajas", self)
            cajas_action.triggered.connect(self.abrir_crud_cajas)
            admin_menu.addAction(cajas_action)
            
            cat_action = QAction("Gestionar Categorías", self)
            cat_action.triggered.connect(self.abrir_crud_categorias)
            admin_menu.addAction(cat_action)

        # --- Main Widget ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setCentralWidget(main_widget)

        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Control de Caja Chica")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        
        user_info = f"Usuario: <b>{self.username}</b> ({self.rol}) | Caja: <b>{self.caja_nombre}</b>"
        user_label = QLabel(user_info)
        user_label.setFont(QFont("Segoe UI", 10))
        user_label.setAlignment(Qt.AlignRight)
        user_label.setStyleSheet("color: #555;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_label)
        main_layout.addLayout(header_layout)

        # --- Dashboard (Tarjetas de Resumen) ---
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(20)

        self.card_saldo = self.create_dashboard_card("Saldo Actual", "$ 0.00", "#0d6efd") # Azul
        self.card_ingresos = self.create_dashboard_card("Total Ingresos", "$ 0.00", "#198754") # Verde
        self.card_egresos = self.create_dashboard_card("Total Egresos", "$ 0.00", "#dc3545") # Rojo

        dashboard_layout.addWidget(self.card_saldo)
        dashboard_layout.addWidget(self.card_ingresos)
        dashboard_layout.addWidget(self.card_egresos)
        main_layout.addLayout(dashboard_layout)

        # --- Sección de Registro Rápido ---
        registro_group = QFrame()
        registro_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QLabel {
                font-weight: bold;
                color: #495057;
                border: none;
            }
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #86b7fe;
            }
        """)
        registro_layout = QVBoxLayout(registro_group)
        registro_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_registro = QLabel("Registrar Nuevo Movimiento")
        lbl_registro.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_registro.setStyleSheet("color: #212529; border: none; margin-bottom: 5px;")
        registro_layout.addWidget(lbl_registro)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)
        
        # Tipo
        vbox_tipo = QVBoxLayout()
        vbox_tipo.addWidget(QLabel("Tipo:"))
        self.cb_tipo_mov = QComboBox()
        self.cb_tipo_mov.addItems(["Ingreso", "Egreso"])
        self.cb_tipo_mov.setFixedWidth(100)
        self.cb_tipo_mov.currentIndexChanged.connect(self.actualizar_categorias)
        vbox_tipo.addWidget(self.cb_tipo_mov)
        form_layout.addLayout(vbox_tipo)
        
        # Categoría
        vbox_cat = QVBoxLayout()
        vbox_cat.addWidget(QLabel("Categoría:"))
        self.cb_categoria = QComboBox()
        self.cb_categoria.setFixedWidth(180)
        vbox_cat.addWidget(self.cb_categoria)
        form_layout.addLayout(vbox_cat)
        
        # Concepto
        vbox_desc = QVBoxLayout()
        vbox_desc.addWidget(QLabel("Concepto / Descripción:"))
        self.le_descripcion = QLineEdit()
        self.le_descripcion.setPlaceholderText("Detalle del movimiento...")
        vbox_desc.addWidget(self.le_descripcion)
        form_layout.addLayout(vbox_desc, stretch=2)
        
        # Monto (QLineEdit con validador)
        vbox_monto = QVBoxLayout()
        vbox_monto.addWidget(QLabel("Monto ($):"))
        self.le_monto = QLineEdit()
        self.le_monto.setPlaceholderText("0.00")
        self.le_monto.setFixedWidth(100)
        self.le_monto.setAlignment(Qt.AlignRight)
        # Validar solo números y un punto decimal
        regex = QRegularExpression(r"^\d{0,7}(\.\d{0,2})?$")
        validator = QRegularExpressionValidator(regex, self.le_monto)
        self.le_monto.setValidator(validator)
        vbox_monto.addWidget(self.le_monto)
        form_layout.addLayout(vbox_monto)
        
        # Botón Guardar
        vbox_btn = QVBoxLayout()
        vbox_btn.addWidget(QLabel("")) # Espaciador para alinear abajo
        self.btn_guardar_mov = QPushButton("Registrar")
        self.btn_guardar_mov.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_mov.setFixedHeight(32)
        self.btn_guardar_mov.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        self.btn_guardar_mov.clicked.connect(self.guardar_movimiento)
        vbox_btn.addWidget(self.btn_guardar_mov)
        form_layout.addLayout(vbox_btn)

        registro_layout.addLayout(form_layout)
        main_layout.addWidget(registro_group)

        # --- Tabla de Movimientos ---
        lbl_historial = QLabel("Historial de Movimientos")
        lbl_historial.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_historial.setStyleSheet("margin-top: 10px;")
        main_layout.addWidget(lbl_historial)

        self.table_movimientos = QTableWidget()
        self.table_movimientos.setColumnCount(7)
        self.table_movimientos.setHorizontalHeaderLabels(["ID", "Fecha", "Tipo", "Categoría", "Concepto", "Monto", "Usuario"])
        self.table_movimientos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_movimientos.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_movimientos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_movimientos.setAlternatingRowColors(True)
        self.table_movimientos.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                gridline-color: #e9ecef;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 4px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Habilitar menú contextual (click derecho)
        self.table_movimientos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_movimientos.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        main_layout.addWidget(self.table_movimientos)

    def create_dashboard_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                color: white;
            }}
        """)
        card.setFixedHeight(80)
        layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10))
        lbl_title.setStyleSheet("background: transparent; border: none;")
        
        lbl_value = QLabel(value)
        lbl_value.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_value.setStyleSheet("background: transparent; border: none;")
        lbl_value.setAlignment(Qt.AlignRight)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        
        # Guardar referencia al label de valor para actualizarlo después
        if title == "Saldo Actual":
            self.lbl_saldo_val = lbl_value
        elif title == "Total Ingresos":
            self.lbl_ingresos_val = lbl_value
        elif title == "Total Egresos":
            self.lbl_egresos_val = lbl_value
            
        return card

    def inicializar_sesion(self):
        """
        Verifica si existe una sesión abierta para esta caja.
        Si no, crea una nueva sesión automáticamente.
        """
        try:
            # Buscar sesión abierta
            query = "SELECT id FROM sesiones_caja WHERE caja_id = %s AND estado = 'Abierta' ORDER BY id DESC LIMIT 1"
            result = self.db.execute_query(query, (self.caja_id,))
            
            if result:
                self.sesion_id = result[0]['id']
                logging.info(f"[MAIN_WINDOW] Sesión existente encontrada. ID: {self.sesion_id}")
            else:
                # Crear nueva sesión
                logging.info(f"[MAIN_WINDOW] No hay sesión abierta para la caja {self.caja_id}. Creando nueva sesión automática.")
                query_insert = """
                    INSERT INTO sesiones_caja (caja_id, usuario_id, fecha_apertura, monto_inicial, estado)
                    VALUES (%s, %s, NOW(), 0.00, 'Abierta')
                """
                self.sesion_id = self.db.execute_query(query_insert, (self.caja_id, self.usuario_id))
                logging.info(f"[MAIN_WINDOW] Nueva sesión creada exitosamente. ID: {self.sesion_id}")
                
        except Exception as e:
            logging.critical(f"[MAIN_WINDOW] Error crítico al inicializar sesión: {e}")
            QMessageBox.critical(self, "Error Crítico", "No se pudo inicializar la sesión de caja. La aplicación se cerrará.")
            self.close()

    def load_initial_data(self):
        logging.info("[MAIN_WINDOW] Cargando datos iniciales (movimientos, saldo, categorías).")
        self.actualizar_categorias()
        self.cargar_movimientos()

    def actualizar_categorias(self):
        tipo = self.cb_tipo_mov.currentText()
        query = "SELECT id, nombre FROM categorias_movimiento WHERE tipo = %s ORDER BY nombre"
        categorias = self.db.execute_query(query, (tipo,))
        
        self.cb_categoria.clear()
        if categorias:
            for cat in categorias:
                self.cb_categoria.addItem(cat['nombre'], userData=cat['id'])
        else:
            logging.warning(f"[MAIN_WINDOW] No se encontraron categorías para el tipo '{tipo}'.")

    def cargar_movimientos(self):
        # Consulta adaptada al esquema real: usa sesiones_caja para filtrar por caja
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto, u.username
            FROM movimientos_caja m
            JOIN sesiones_caja s ON m.sesion_id = s.id
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.caja_id = %s
            ORDER BY m.fecha_hora DESC, m.id DESC
        """
        movimientos = self.db.execute_query(query, (self.caja_id,)) or []
        
        self.table_movimientos.setRowCount(len(movimientos))
        for row, mov in enumerate(movimientos):
            self.table_movimientos.setItem(row, 0, QTableWidgetItem(str(mov['id'])))
            self.table_movimientos.setItem(row, 1, QTableWidgetItem(mov['fecha_hora'].strftime('%Y-%m-%d %H:%M')))
            
            item_tipo = QTableWidgetItem(mov['tipo'])
            if mov['tipo'] == 'Ingreso':
                item_tipo.setForeground(QColor("#198754")) # Verde
            else:
                item_tipo.setForeground(QColor("#dc3545")) # Rojo
            self.table_movimientos.setItem(row, 2, item_tipo)
            
            self.table_movimientos.setItem(row, 3, QTableWidgetItem(mov['categoria']))
            self.table_movimientos.setItem(row, 4, QTableWidgetItem(mov['concepto']))
            self.table_movimientos.setItem(row, 5, QTableWidgetItem(f"${mov['monto']:.2f}"))
            self.table_movimientos.setItem(row, 6, QTableWidgetItem(mov['username']))
            
        self.calcular_totales()

    def calcular_totales(self):
        # Calcular Ingresos
        query_ingresos = """
            SELECT COALESCE(SUM(m.monto), 0) as total
            FROM movimientos_caja m 
            JOIN sesiones_caja s ON m.sesion_id = s.id 
            WHERE m.tipo = 'Ingreso' AND s.caja_id = %s
        """
        res_ing = self.db.execute_query(query_ingresos, (self.caja_id,))
        total_ingresos = float(res_ing[0]['total']) if res_ing else 0.0
        
        # Calcular Egresos
        query_egresos = """
            SELECT COALESCE(SUM(m.monto), 0) as total
            FROM movimientos_caja m 
            JOIN sesiones_caja s ON m.sesion_id = s.id 
            WHERE m.tipo = 'Egreso' AND s.caja_id = %s
        """
        res_egr = self.db.execute_query(query_egresos, (self.caja_id,))
        total_egresos = float(res_egr[0]['total']) if res_egr else 0.0
        
        saldo = total_ingresos - total_egresos
        
        # Actualizar Dashboard
        self.lbl_ingresos_val.setText(f"$ {total_ingresos:,.2f}")
        self.lbl_egresos_val.setText(f"$ {total_egresos:,.2f}")
        self.lbl_saldo_val.setText(f"$ {saldo:,.2f}")

    def guardar_movimiento(self):
        if not self.sesion_id:
            QMessageBox.critical(self, "Error", "No hay una sesión activa. Reinicie la aplicación.")
            return

        tipo = self.cb_tipo_mov.currentText()
        categoria_id = self.cb_categoria.currentData()
        concepto = self.le_descripcion.text().strip()
        monto_str = self.le_monto.text().strip()
        
        if not all([tipo, categoria_id, concepto, monto_str]):
            QMessageBox.warning(self, "Campos Incompletos", "Por favor, complete todos los campos.")
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor a 0")
        except ValueError:
            QMessageBox.warning(self, "Monto Inválido", "Por favor, ingrese un monto válido.")
            return

        try:
            # Insertar usando el esquema correcto: sesion_id, fecha_hora, concepto
            query = """
                INSERT INTO movimientos_caja (sesion_id, categoria_id, tipo, concepto, monto, fecha_hora)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            params = (self.sesion_id, categoria_id, tipo, concepto, monto)
            
            self.db.execute_query(query, params)
            logging.info(f"[MAIN_WINDOW] Movimiento registrado por '{self.username}': {tipo} de ${monto} en categoría ID {categoria_id}.")
            
            QMessageBox.information(self, "Éxito", "Movimiento registrado correctamente.")
            self.limpiar_form_movimiento()
            self.cargar_movimientos()

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo guardar el movimiento: {e}")
            logging.error(f"[MAIN_WINDOW] Error al guardar movimiento: {e}", exc_info=True)

    def limpiar_form_movimiento(self):
        self.le_descripcion.clear()
        self.le_monto.clear()
        self.le_descripcion.setFocus()

    def mostrar_menu_contextual(self, position):
        menu = QMenu()
        
        action_eliminar = QAction("Eliminar Movimiento", self)
        action_imprimir = QAction("Imprimir Vale / Recibo", self)
        
        action_eliminar.triggered.connect(self.eliminar_movimiento)
        action_imprimir.triggered.connect(self.imprimir_vale)
        
        menu.addAction(action_imprimir)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
        menu.exec(self.table_movimientos.viewport().mapToGlobal(position))

    def eliminar_movimiento(self):
        selected = self.table_movimientos.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        mov_id = self.table_movimientos.item(row, 0).text()
        concepto = self.table_movimientos.item(row, 4).text()
        
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       f"¿Está seguro de eliminar el movimiento ID {mov_id}?\nConcepto: {concepto}",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            try:
                query = "DELETE FROM movimientos_caja WHERE id = %s"
                self.db.execute_query(query, (mov_id,))
                logging.info(f"[MAIN_WINDOW] Movimiento ID {mov_id} eliminado por usuario '{self.username}'.")
                self.cargar_movimientos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el movimiento: {e}")
                logging.error(f"[MAIN_WINDOW] Error eliminando movimiento ID {mov_id}: {e}")

    def imprimir_vale(self):
        selected = self.table_movimientos.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        mov_id = self.table_movimientos.item(row, 0).text()
        
        # Obtener datos completos del movimiento para el reporte
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            WHERE m.id = %s
        """
        data = self.db.execute_query(query, (mov_id,))
        
        if data:
            mov_data = data[0]
            filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Vale", f"vale_{mov_id}.pdf", "PDF (*.pdf)")
            if filepath:
                try:
                    generar_vale_pdf(mov_data, filepath)
                    QMessageBox.information(self, "Éxito", f"Vale generado en:\n{filepath}")
                    logging.info(f"[MAIN_WINDOW] Vale generado para movimiento ID {mov_id}.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error generando PDF: {e}")
                    logging.error(f"[MAIN_WINDOW] Error generando vale PDF: {e}")

    def mostrar_dialogo_reporte(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Generar Reporte de Movimientos")
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        self.report_start_date = QDateEdit(QDate.currentDate().addDays(-7))
        self.report_end_date = QDateEdit(QDate.currentDate())
        self.report_start_date.setCalendarPopup(True)
        self.report_end_date.setCalendarPopup(True)
        form.addRow("Fecha de Inicio:", self.report_start_date)
        form.addRow("Fecha de Fin:", self.report_end_date)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_generar = QPushButton("Generar PDF")
        btn_generar.clicked.connect(lambda: self.generar_reporte(dialog))
        btn_box.addStretch()
        btn_box.addWidget(btn_generar)
        layout.addLayout(btn_box)
        
        dialog.exec()

    def generar_reporte(self, dialog):
        start_date = self.report_start_date.date().toString("yyyy-MM-dd")
        end_date = self.report_end_date.date().toString("yyyy-MM-dd")
        
        logging.info(f"[MAIN_WINDOW] Solicitado reporte PDF desde {start_date} hasta {end_date} para la caja ID {self.caja_id}.")

        query = """
            SELECT m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto, u.username as usuario, c_caja.nombre as caja
            FROM movimientos_caja m
            JOIN sesiones_caja s ON m.sesion_id = s.id
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            JOIN usuarios u ON s.usuario_id = u.id
            JOIN configuracion_caja c_caja ON s.caja_id = c_caja.id
            WHERE s.caja_id = %s AND DATE(m.fecha_hora) BETWEEN %s AND %s
            ORDER BY m.fecha_hora
        """
        try:
            data = self.db.execute_query(query, (self.caja_id, start_date, end_date))
            
            if not data:
                QMessageBox.warning(self, "Sin Datos", "No se encontraron movimientos en el rango de fechas seleccionado.")
                logging.warning("[MAIN_WINDOW] Reporte vacío: No hay datos en el rango seleccionado.")
                return

            filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", f"reporte_{start_date}_a_{end_date}.pdf", "PDF (*.pdf)")
            
            if filepath:
                info_extra = {
                    'desde': start_date,
                    'hasta': end_date,
                    'usuario': self.username
                }
                
                generar_listado_pdf(
                    movimientos_list=data,
                    info_extra=info_extra,
                    output_path=filepath
                )
                
                QMessageBox.information(self, "Éxito", f"Reporte generado en:\n{filepath}")
                logging.info(f"[MAIN_WINDOW] Reporte PDF generado exitosamente en {filepath}.")
            else:
                logging.warning("[MAIN_WINDOW] Generación de reporte cancelada por el usuario.")
            
            dialog.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte: {e}")
            logging.error(f"[MAIN_WINDOW] Error al generar reporte: {e}", exc_info=True)

    def abrir_crud_usuarios(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de usuarios.")
        dialog = CrudUsuarios(self.db, self)
        dialog.exec()
        logging.info("[MAIN_WINDOW] Cerrada ventana de gestión de usuarios.")
        self.load_initial_data()

    def abrir_crud_cajas(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de cajas.")
        dialog = CrudCajas(self.db, self)
        dialog.exec()
        logging.info("[MAIN_WINDOW] Cerrada ventana de gestión de cajas.")
        self.load_initial_data()

    def abrir_crud_categorias(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de categorías.")
        dialog = CrudCategorias(self.db, self)
        dialog.exec()
        logging.info("[MAIN_WINDOW] Cerrada ventana de gestión de categorías.")
        self.load_initial_data()

    def closeEvent(self, event):
        logging.info("[MAIN_WINDOW] Solicitud de cierre de la aplicación.")
        super().closeEvent(event)
