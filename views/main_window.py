# *****************************************************************************
#
#   Sistema:    C5          -   Módulo de Caja Chica
#   Módulo:     main_window -   Ventana Principal de la Aplicación
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   ...
#   16 |07/03/2026| Antigravity/Addy López |Corrección de INSERT en movimientos_caja.
# *****************************************************************************
#
import logging
import os
from decimal import Decimal

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QDateEdit, QFileDialog, QMessageBox, QDialog, QFormLayout, QFrame, QMenu, QApplication
)
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QFont, QAction, QRegularExpressionValidator, QColor
from database.connection import DatabaseConnection
from views.crud_cajas import CrudCajas
from views.crud_categorias import CrudCategorias
from views.crud_usuarios import CrudUsuarios
from views.crud_empresa import CrudEmpresa
from views.report_viewer import ReportViewerWindow
from views.modal_cierre import ModalCierre
from utils.export_pdf import generar_listado_pdf, generar_vale_pdf

class MainWindow(QMainWindow):
    def __init__(self, usuario_id, username, rol, caja_id, caja_nombre):
        super().__init__()

        # Inicialización de variables de instancia
        self.card_saldo = self.btn_guardar_mov = self.table_movimientos = self.btn_cierre = self.lbl_saldo_val = None
        self.lbl_ingresos_val = self.lbl_egresos_val = self.report_start_date = self.report_end_date = None
        self.card_ingresos = self.card_egresos = self.cb_tipo_mov = self.cb_categoria = self.le_descripcion = None
        self.le_monto = None # Inicializar como None, no como Decimal
        self.lbl_inicial_sesion_val = None

        logging.info("[MAIN_WINDOW] Entrando al programa (Ventana Principal).")

        self.usuario_id = usuario_id
        self.username = username
        self.rol = rol
        self.caja_id = caja_id
        self.caja_nombre = caja_nombre
        self.sesion_id = None 
        self.simbolo_moneda = "$" # Valor por defecto
        self.fondo_fijo = 0.0 # Este ahora representará el saldo inicial de la caja (cierre anterior o fondo fijo)
        self.saldo_actual_caja = 0.0 # Variable para mantener el saldo actual
        
        self.db = DatabaseConnection()
        
        self.setWindowTitle("C5 - Módulo de Caja Chica")
        self.center_and_resize(0.8)
        
        self.cargar_parametros_empresa()
        self.cargar_saldo_inicial_caja() # Renombrado para mayor claridad
        self.setup_ui()
        self.inicializar_sesion()
        self.load_initial_data()

    def center_and_resize(self, factor):
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * factor)
        height = int(screen.height() * factor)
        self.resize(width, height)
        self.move(screen.center() - self.rect().center())

    def cargar_parametros_empresa(self):
        """Carga el símbolo de moneda desde la base de datos."""
        try:
            query = "SELECT simbolo_moneda FROM parametros_control WHERE id = 1"
            res = self.db.execute_query(query)
            if res:
                self.simbolo_moneda = res[0].get('simbolo_moneda', '')
                if self.simbolo_moneda is None:
                    self.simbolo_moneda = ""
        except Exception as e:
            logging.error(f"[MAIN_WINDOW] Error cargando parámetros de empresa: {e}")

    def cargar_saldo_inicial_caja(self):
        """
        Carga el saldo inicial de la caja.
        Prioriza el saldo_inicial (del cierre anterior) de la tabla configuracion_caja,
        si no existe, usa el fondo_fijo de la misma tabla.
        """
        try:
            query = "SELECT saldo_inicial, fondo_fijo FROM configuracion_caja WHERE id = %s"
            res = self.db.execute_query(query, (self.caja_id,))
            if res:
                saldo_inicial_db = res[0].get('saldo_inicial')
                fondo_fijo_db = float(res[0].get('fondo_fijo', 0.0))
                
                if saldo_inicial_db is not None:
                    self.fondo_fijo = float(saldo_inicial_db)
                else:
                    self.fondo_fijo = fondo_fijo_db
                
                logging.info(f"[MAIN_WINDOW] Saldo inicial de caja {self.caja_id} cargado: {self.fondo_fijo}")
            else:
                logging.warning(f"[MAIN_WINDOW] No se encontró configuración para la caja {self.caja_id}. Usando fondo fijo 0.0.")
                self.fondo_fijo = 0.0 # Fallback si no se encuentra la caja
        except Exception as e:
            logging.error(f"[MAIN_WINDOW] Error cargando saldo inicial de caja {self.caja_id}: {e}")
            self.fondo_fijo = 0.0 # Asegurar un valor por defecto en caso de error

    def format_money(self, amount):
        """Formatea un monto con el símbolo de moneda configurado."""
        if self.simbolo_moneda:
            return f"{self.simbolo_moneda} {amount:,.2f}"
        else:
            return f"{amount:,.2f}"

    def setup_ui(self):
        """Preparar la ventana con todos sus componentes"""

        # --- Menu Bar ---
        menu_bar = self.menuBar()
        
        # Menu Archivo
        file_menu = menu_bar.addMenu("Archivo")
        
        report_action = QAction("Generar Reporte General", self)
        report_action.triggered.connect(self.mostrar_dialogo_reporte)
        file_menu.addAction(report_action)

        view_reports_action = QAction("Ver Reportes Guardados", self)
        view_reports_action.triggered.connect(self.abrir_report_viewer)
        file_menu.addAction(view_reports_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Administración (solo para Admins)
        if self.rol == "Administrador":
            admin_menu = menu_bar.addMenu("Administración")
            
            empresa_action = QAction("Configuración de Empresa", self)
            empresa_action.triggered.connect(self.abrir_crud_empresa)
            admin_menu.addAction(empresa_action)
            
            admin_menu.addSeparator()

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

        self.card_inicial = self.create_dashboard_card("Fondo Inicial", self.format_money(0.0), "#6c757d") # Gris
        self.card_ingresos = self.create_dashboard_card("Total Ingresos", self.format_money(0.0), "#198754") # Verde
        self.card_egresos = self.create_dashboard_card("Total Egresos", self.format_money(0.0), "#dc3545") # Rojo
        self.card_saldo = self.create_dashboard_card("Saldo Actual", self.format_money(0.0), "#0d6efd") # Azul

        dashboard_layout.addWidget(self.card_inicial)
        dashboard_layout.addWidget(self.card_ingresos)
        dashboard_layout.addWidget(self.card_egresos)
        dashboard_layout.addWidget(self.card_saldo)
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
            QComboBox::item:selected {
                background-color: #0d6efd; /* Azul */
                color: white;
            }
            QComboBox::item:hover {
                background-color: #e9ecef; /* Gris claro al pasar el mouse */
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
        # self.le_descripcion.returnPressed.connect(self.le_monto.setFocus) # MOVIDO AL FINAL
        vbox_desc.addWidget(self.le_descripcion)
        form_layout.addLayout(vbox_desc, stretch=2)
        
        # Monto
        vbox_monto = QVBoxLayout()
        label_monto = f"Monto ({self.simbolo_moneda}):" if self.simbolo_moneda else "Monto:"
        vbox_monto.addWidget(QLabel(label_monto))
        self.le_monto = QLineEdit()
        self.le_monto.setPlaceholderText("0.00")
        self.le_monto.setFixedWidth(100)
        self.le_monto.setAlignment(Qt.AlignRight)
        regex = QRegularExpression(r"^\d{0,7}(\.\d{0,2})?$")
        validator = QRegularExpressionValidator(regex, self.le_monto)
        self.le_monto.setValidator(validator)
        # self.le_monto.returnPressed.connect(self.guardar_movimiento) # MOVIDO AL FINAL
        vbox_monto.addWidget(self.le_monto)
        form_layout.addLayout(vbox_monto)
        
        # Conexiones de Enter (MOVIDAS AQUÍ)
        self.le_descripcion.returnPressed.connect(self.le_monto.setFocus)
        self.le_monto.returnPressed.connect(self.guardar_movimiento)

        # Botón Guardar
        vbox_btn = QVBoxLayout()
        vbox_btn.addWidget(QLabel("")) 
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
        self.btn_guardar_mov.setDefault(True)
        self.btn_guardar_mov.setAutoDefault(True)
        vbox_btn.addWidget(self.btn_guardar_mov)
        form_layout.addLayout(vbox_btn)

        registro_layout.addLayout(form_layout)
        main_layout.addWidget(registro_group)

        # --- Tabla de Movimientos ---
        lbl_historial = QLabel("Historial de Movimientos (Sesión Actual)")
        lbl_historial.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_historial.setStyleSheet("margin-top: 10px;")
        main_layout.addWidget(lbl_historial)

        self.table_movimientos = QTableWidget()
        self.table_movimientos.setColumnCount(6)
        self.table_movimientos.setHorizontalHeaderLabels(["Fecha", "Tipo", "Categoría", "Concepto", "Monto", "Usuario"])
        
        for indice, ancho in enumerate((120, 80, 200, 350, 120, 150), start=0):
            self.table_movimientos.setColumnWidth(indice, ancho)
            
        self.table_movimientos.verticalHeader().setDefaultSectionSize(18)
        self.table_movimientos.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_movimientos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_movimientos.setAlternatingRowColors(True)
        self.table_movimientos.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                gridline-color: #e9ecef;
                font: 10pt "Segoe UI";
                gridline-color: rgb(147, 147, 147);
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 4px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        self.table_movimientos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_movimientos.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        main_layout.addWidget(self.table_movimientos)

        # --- Footer (Botón Cierre) ---
        footer_layout = QHBoxLayout()
        self.btn_cierre = QPushButton("Cerrar Caja")
        self.btn_cierre.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                font-weight: bold; 
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #bb2d3b; }
        """)
        self.btn_cierre.clicked.connect(self.abrir_modal_cierre)
        
        footer_layout.addWidget(self.btn_cierre)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

    def create_dashboard_card(self, title, value, color):
        """Preparar el Dashboard"""

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
        
        if title == "Saldo Actual":
            self.lbl_saldo_val = lbl_value
        elif title == "Total Ingresos":
            self.lbl_ingresos_val = lbl_value
        elif title == "Total Egresos":
            self.lbl_egresos_val = lbl_value
        elif title == "Fondo Inicial":
            self.lbl_inicial_sesion_val = lbl_value
            
        return card

    def inicializar_sesion(self):
        try:
            query = "SELECT id FROM sesiones_caja WHERE caja_id = %s AND estado = 'Abierta' ORDER BY id DESC LIMIT 1"
            result = self.db.execute_query(query, (self.caja_id,))
            
            if result:
                self.sesion_id = result[0]['id']
                logging.info(f"[MAIN_WINDOW] Sesión existente encontrada. ID: {self.sesion_id}")
            else:
                # No hay sesión abierta, buscar el saldo final de la última sesión cerrada
                query_last_session = """SELECT monto_final_fisico 
                                            FROM sesiones_caja 
                                                WHERE caja_id = %s AND estado = 'Cerrada' 
                                                    ORDER BY fecha_cierre DESC LIMIT 1
                                    """
                last_session = self.db.execute_query(query_last_session, (self.caja_id,))

                if last_session:
                    monto_inicial = float(last_session[0]['monto_final_fisico'])
                else:
                    # Si nunca ha habido una sesión, usar el saldo inicial de la caja (fondo fijo o saldo anterior)
                    monto_inicial = self.fondo_fijo

                logging.info(f"[MAIN_WINDOW] Creando nueva sesión para caja {self.caja_id} con monto inicial de {monto_inicial}.")

                query_insert = """
                                INSERT INTO sesiones_caja (caja_id, usuario_id, fecha_apertura, monto_inicial, estado)
                                VALUES (%s, %s, NOW(), %s, 'Abierta')
                               """
                self.sesion_id = self.db.execute_query(query_insert, (self.caja_id, self.usuario_id, monto_inicial)) # CORRECCIÓN AQUÍ
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
        # Filtrar SOLO por la sesión actual
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto, u.username
            FROM movimientos_caja m
            JOIN sesiones_caja s ON m.sesion_id = s.id
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE m.sesion_id = %s
            ORDER BY m.fecha_hora DESC, m.id DESC
        """
        movimientos = self.db.execute_query(query, (self.sesion_id,)) or []
        
        self.table_movimientos.setRowCount(len(movimientos))
        for row, mov in enumerate(movimientos):
            item_fecha = QTableWidgetItem(mov['fecha_hora'].strftime('%Y-%m-%d %H:%M'))
            item_fecha.setData(Qt.UserRole, mov['id'])
            self.table_movimientos.setItem(row, 0, item_fecha)
            self.table_movimientos.item(row, 0).setTextAlignment(Qt.AlignCenter)
            
            item_tipo = QTableWidgetItem(mov['tipo'])
            if mov['tipo'] == 'Ingreso':
                item_tipo.setForeground(QColor("#198754"))
            else:
                item_tipo.setForeground(QColor("#dc3545"))
            self.table_movimientos.setItem(row, 1, item_tipo)
            self.table_movimientos.item(row, 1).setTextAlignment(Qt.AlignCenter)
            
            self.table_movimientos.setItem(row, 2, QTableWidgetItem(mov['categoria']))
            self.table_movimientos.setItem(row, 3, QTableWidgetItem(mov['concepto']))
            
            self.table_movimientos.setItem(row, 4, QTableWidgetItem(self.format_money(mov['monto'])))
            self.table_movimientos.item(row, 4).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            self.table_movimientos.setItem(row, 5, QTableWidgetItem(mov['username']))
            
        self.calcular_totales()

    def calcular_totales(self):
        # Obtener el monto inicial de la sesión
        query_monto_inicial = "SELECT monto_inicial FROM sesiones_caja WHERE id = %s"
        res_inicial = self.db.execute_query(query_monto_inicial, (self.sesion_id,))
        monto_inicial_sesion = float(res_inicial[0]['monto_inicial']) if res_inicial else 0.0

        # Totales SOLO de la sesión actual
        query_ingresos = """
            SELECT COALESCE(SUM(monto), 0) as total
            FROM movimientos_caja 
            WHERE tipo = 'Ingreso' AND sesion_id = %s AND anulado = FALSE
        """
        res_ing = self.db.execute_query(query_ingresos, (self.sesion_id,))
        total_ingresos = float(res_ing[0]['total']) if res_ing else 0.0
        
        query_egresos = """
            SELECT COALESCE(SUM(monto), 0) as total
            FROM movimientos_caja 
            WHERE tipo = 'Egreso' AND sesion_id = %s AND anulado = FALSE
        """
        res_egr = self.db.execute_query(query_egresos, (self.sesion_id,))
        total_egresos = float(res_egr[0]['total']) if res_egr else 0.0
        
        # Saldo actual de la sesión = Monto Inicial de la Sesión + Ingresos - Egresos
        self.saldo_actual_caja = monto_inicial_sesion + total_ingresos - total_egresos
        
        # Actualizar Dashboard
        self.lbl_inicial_sesion_val.setText(self.format_money(monto_inicial_sesion))
        self.lbl_ingresos_val.setText(self.format_money(total_ingresos))
        self.lbl_egresos_val.setText(self.format_money(total_egresos))
        self.lbl_saldo_val.setText(self.format_money(self.saldo_actual_caja))

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

        # --- Validación de Saldo ---
        if tipo == 'Egreso':
            if monto > self.saldo_actual_caja:
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Saldo Insuficiente", 
                                      f"No puede registrar un egreso de {self.format_money(monto)} porque el saldo actual es de solo {self.format_money(self.saldo_actual_caja)}.",
                                      QMessageBox.StandardButton.Ok, self)
                msg_box.button(QMessageBox.StandardButton.Ok).setText("Aceptar")
                msg_box.exec()
                return
        # --- Fin de Validación ---

        try:
            query = """
                INSERT INTO movimientos_caja (sesion_id, usuario_id, caja_id, categoria_id, tipo, concepto, monto, fecha_hora)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = (self.sesion_id, self.usuario_id, self.caja_id, categoria_id, tipo, concepto, monto)
            
            result = self.db.execute_query(query, params)
            
            if result is not None:
                logging.info(f"[MAIN_WINDOW] Movimiento registrado por '{self.username}': {tipo} de {self.format_money(monto)} en categoría ID {categoria_id}.")
                self.limpiar_form_movimiento()
                self.cargar_movimientos()
            else:
                QMessageBox.critical(self, "Error de Base de Datos", "No se pudo guardar el movimiento.")

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo guardar el movimiento: {e}")
            logging.error(f"[MAIN_WINDOW] Error al guardar movimiento: {e}", exc_info=True)

    def limpiar_form_movimiento(self):
        self.le_descripcion.clear()
        self.le_monto.clear()
        self.le_descripcion.setFocus()

    def mostrar_menu_contextual(self, position):
        selected_items = self.table_movimientos.selectedItems()
        if not selected_items:
            return

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
        mov_id = self.table_movimientos.item(row, 0).data(Qt.UserRole)
        concepto = self.table_movimientos.item(row, 3).text()
        
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       f"¿Está seguro de eliminar el movimiento ID {mov_id}?\nConcepto: {concepto}",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
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
        mov_id = self.table_movimientos.item(row, 0).data(Qt.UserRole)
        
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            WHERE m.id = %s
        """
        data = self.db.execute_query(query, (mov_id,))
        
        if data:
            mov_data = data[0]
            
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            fecha_str = mov_data['fecha_hora'].strftime('%Y-%m-%d')
            caja_nombre_safe = "".join(x for x in self.caja_nombre if x.isalnum() or x in " -_").rstrip()
            filename = f"vale_{mov_id}_{fecha_str}_{caja_nombre_safe}.pdf"
            filepath = os.path.join(reports_dir, filename)

            try:
                # Pasar parámetros de empresa (moneda)
                parametros = {'simbolo_moneda': self.simbolo_moneda}
                generar_vale_pdf(mov_data, filepath, parametros=parametros)
                logging.info(f"[MAIN_WINDOW] Vale generado para movimiento ID {mov_id} en {filepath}.")
                os.startfile(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error generando o abriendo PDF: {e}")
                logging.error(f"[MAIN_WINDOW] Error generando/abriendo vale PDF: {e}")

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

            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            caja_nombre_safe = "".join(x for x in self.caja_nombre if x.isalnum() or x in " -_").rstrip()
            filename = f"reporte-general_{start_date}_a_{end_date}_{caja_nombre_safe}.pdf"
            filepath = os.path.join(reports_dir, filename)
            
            info_extra = {
                'desde': start_date,
                'hasta': end_date,
                'usuario': self.username
            }
            
            # Pasar parámetros de empresa (moneda)
            parametros = {'simbolo_moneda': self.simbolo_moneda}
            generar_listado_pdf(
                movimientos_list=data,
                info_extra=info_extra,
                output_path=filepath,
                parametros=parametros
            )
            
            logging.info(f"[MAIN_WINDOW] Reporte PDF generado exitosamente en {filepath}.")
            os.startfile(filepath)
            dialog.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte: {e}")
            logging.error(f"[MAIN_WINDOW] Error al generar reporte: {e}", exc_info=True)

    def abrir_report_viewer(self):
        logging.info("[MAIN_WINDOW] Abriendo visor de reportes.")
        dialog = ReportViewerWindow(self.rol, self.caja_nombre, self)
        dialog.exec()
        logging.info("[MAIN_WINDOW] Cerrado visor de reportes.")

    def abrir_crud_empresa(self):
        logging.info("[MAIN_WINDOW] Abriendo configuración de empresa.")
        dialog = CrudEmpresa(self.db, self)
        dialog.exec()
        # Recargar parámetros por si cambiaron (ej. símbolo de moneda)
        self.cargar_parametros_empresa()
        self.load_initial_data() # Refrescar UI con nuevo símbolo

    def abrir_crud_usuarios(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de usuarios.")
        dialog = CrudUsuarios(self.db, self)
        dialog.exec()
        self.load_initial_data() 

    def abrir_crud_cajas(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de cajas.")
        dialog = CrudCajas(self.db, self)
        dialog.exec()
        self.load_initial_data()

    def abrir_crud_categorias(self):
        logging.info("[MAIN_WINDOW] Abriendo ventana de gestión de categorías.")
        dialog = CrudCategorias(self.db, self)
        dialog.exec()
        self.load_initial_data()

    def abrir_modal_cierre(self):
        logging.info("[MAIN_WINDOW] Abriendo modal de cierre de caja.")
        # Pasar el símbolo de moneda al modal de cierre
        dialog = ModalCierre(self.db, self.sesion_id, self.simbolo_moneda, self.caja_nombre, self.username, self)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            logging.info("[MAIN_WINDOW] Caja cerrada exitosamente. Cerrando aplicación.")
            self.close()

    def closeEvent(self, event):
        logging.info("[MAIN_WINDOW] Solicitud de cierre de la aplicación.")
        super().closeEvent(event)
