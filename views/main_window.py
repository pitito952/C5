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
    QDateEdit, QFileDialog, QMessageBox, QDialog, QFormLayout, QFrame, QMenu, QApplication, QGridLayout,
    QAbstractItemView
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
from utils.reporte_categorias import generar_reporte_por_categoria

class MainWindow(QMainWindow):
    def __init__(self, usuario_id, username, rol, caja_id, caja_nombre):
        super().__init__()

        # Inicialización de variables de instancia para widgets
        self.card_inicial = None
        self.card_saldo = self.btn_guardar_mov = self.table_movimientos = self.btn_cierre = self.lbl_saldo_val = None
        self.lbl_ingresos_val = self.lbl_egresos_val = self.report_start_date = self.report_end_date = None
        self.card_ingresos = self.card_egresos = self.cb_tipo_mov = self.cb_categoria = self.le_descripcion = None
        self.le_monto = self.le_comprobante = None
        self.lbl_inicial_sesion_val = None

        logging.info("[MAIN_WINDOW] Entrando al programa (Ventana Principal).")

        # Atributos de sesión y de negocio
        self.usuario_id = usuario_id
        self.username = username
        self.rol = rol
        self.caja_id = caja_id
        self.caja_nombre = caja_nombre
        self.sesion_id = None 
        self.simbolo_moneda = "$" # Valor por defecto
        self.nombre_empresa = "Ni Empresa"  # Valor por defecto
        self.ruta_logo = ""
        self.fondo_fijo = 0.0
        self.saldo_actual_caja = 0.0
        
        self.db = DatabaseConnection()
        
        self.setWindowTitle("C5 - Módulo de Caja Chica")
        self.center_and_resize(0.8)
        
        # Carga de datos y configuración inicial
        self.cargar_parametros_empresa()
        self.cargar_saldo_inicial_caja()
        self.setup_ui()
        self.inicializar_sesion()
        self.load_initial_data()

    def center_and_resize(self, factor):
        """Centra y ajusta el tamaño de la ventana según un factor de la pantalla."""
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * factor)
        height = int(screen.height() * factor)
        self.resize(width, height)
        self.move(screen.center() - self.rect().center())

    def cargar_parametros_empresa(self):
        """Carga el símbolo de moneda desde la base de datos."""
        try:
            query = "SELECT simbolo_moneda, nombre_empresa, ruta_logo FROM parametros_control WHERE id = 1"
            res = self.db.execute_query(query)
            if res:
                self.simbolo_moneda = res[0].get('simbolo_moneda', '') or ""
                self.nombre_empresa = res[0].get('nombre_empresa', '') or "Mi Empresa"
                self.ruta_logo = res[0].get('ruta_logo', '') or ''
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
                self.fondo_fijo = float(saldo_inicial_db) if saldo_inicial_db is not None else fondo_fijo_db
                
                logging.info(f"[MAIN_WINDOW] Saldo inicial de caja {self.caja_id} cargado: {self.fondo_fijo}")
            else:
                logging.warning(f"[MAIN_WINDOW] No se encontró configuración para la caja {self.caja_id}. Usando fondo fijo 0.0.")
                self.fondo_fijo = 0.0
        except Exception as e:
            logging.error(f"[MAIN_WINDOW] Error cargando saldo inicial de caja {self.caja_id}: {e}")
            self.fondo_fijo = 0.0

    def format_money(self, amount):
        """Formatea un monto con el símbolo de moneda configurado."""
        return f"{self.simbolo_moneda} {amount:,.2f}" if self.simbolo_moneda else f"{amount:,.2f}"

    def setup_ui(self):
        """Prepara la ventana con todos sus componentes."""
        # --- Main Widget and Layout ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setCentralWidget(main_widget)

        # --- Menu Bar ---
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Archivo")
        
        report_action = QAction("Reporte de Movimientos por Fecha", self)
        report_action.triggered.connect(self.mostrar_dialogo_reporte)
        file_menu.addAction(report_action)

        report_cat_action = QAction("Reporte de Movimientos por Categoría y Fecha", self)
        report_cat_action.triggered.connect(self.mostrar_dialogo_reporte_categoria)
        file_menu.addAction(report_cat_action)

        view_reports_action = QAction("Consulta/Reporte de Comprobantes/Vales", self)
        view_reports_action.triggered.connect(self.abrir_report_viewer)
        file_menu.addAction(view_reports_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # --- Menu Administración (solo para Admins) ---
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

        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Control de Caja Chica")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        user_info = f"Usuario: <b>{self.username}</b> ({self.rol}) | Caja: <b>{self.caja_nombre}</b>"
        user_label = QLabel(user_info)
        user_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_label)
        main_layout.addLayout(header_layout)

        # --- Dashboard (Tarjetas de Resumen) ---
        dashboard_layout = QHBoxLayout()
        self.card_inicial = self.create_dashboard_card("Fondo Inicial", self.format_money(0.0), "#6c757d")
        self.card_ingresos = self.create_dashboard_card("Total Ingresos", self.format_money(0.0), "#198754")
        self.card_egresos = self.create_dashboard_card("Total Egresos", self.format_money(0.0), "#dc3545")
        self.card_saldo = self.create_dashboard_card("Saldo Actual", self.format_money(0.0), "#0d6efd")
        dashboard_layout.addWidget(self.card_inicial)
        dashboard_layout.addWidget(self.card_ingresos)
        dashboard_layout.addWidget(self.card_egresos)
        dashboard_layout.addWidget(self.card_saldo)
        main_layout.addLayout(dashboard_layout)

        # --- Sección de Registro Rápido ---
        registro_group = QFrame()
        registro_group.setStyleSheet("QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; }")
        registro_layout = QVBoxLayout(registro_group)
        
        lbl_registro = QLabel("Registrar Nuevo Movimiento")
        lbl_registro.setFont(QFont("Segoe UI", 11, QFont.Bold))
        registro_layout.addWidget(lbl_registro)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        # Widgets del formulario
        self.cb_tipo_mov = QComboBox()
        self.cb_tipo_mov.setPlaceholderText("Tipo")
        self.cb_tipo_mov.addItems(["Ingreso", "Egreso"])
        self.cb_tipo_mov.setFixedWidth(100)
        self.cb_tipo_mov.currentIndexChanged.connect(self.actualizar_categorias)

        self.cb_categoria = QComboBox()
        self.cb_categoria.setPlaceholderText("Categoría")
        self.cb_categoria.setFixedWidth(180)

        self.le_descripcion = QLineEdit()
        self.le_descripcion.setPlaceholderText("Concepto / Descripción...")

        self.le_comprobante = QLineEdit()
        self.le_comprobante.setPlaceholderText("Comp. (Ej: F123)")
        self.le_comprobante.setFixedWidth(120)

        self.le_monto = QLineEdit()
        self.le_monto.setPlaceholderText("Monto")
        self.le_monto.setFixedWidth(100)
        self.le_monto.setAlignment(Qt.AlignRight)
        self.le_monto.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,7}(\.\d{0,2})?$")))

        self.btn_guardar_mov = QPushButton("Registrar")
        self.btn_guardar_mov.setFixedHeight(32)
        self.btn_guardar_mov.setStyleSheet("background-color: #0d6efd; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 0 15px;")
        self.btn_guardar_mov.setDefault(True)
        self.btn_guardar_mov.setAutoDefault(True)

        # Añadir widgets al layout
        form_layout.addWidget(self.cb_tipo_mov)
        form_layout.addWidget(self.cb_categoria)
        form_layout.addWidget(self.le_descripcion, 1) # Stretch factor
        form_layout.addWidget(self.le_comprobante)
        form_layout.addWidget(self.le_monto)
        form_layout.addWidget(self.btn_guardar_mov)
        
        registro_layout.addLayout(form_layout)
        main_layout.addWidget(registro_group)

        # Conexiones de Enter
        self.le_descripcion.returnPressed.connect(self.le_comprobante.setFocus)
        self.le_comprobante.returnPressed.connect(self.le_monto.setFocus)
        self.le_monto.returnPressed.connect(self.guardar_movimiento)
        self.btn_guardar_mov.clicked.connect(self.guardar_movimiento)

        # --- Tabla de Movimientos ---
        lbl_historial = QLabel("Historial de Movimientos (Sesión Actual)")
        lbl_historial.setFont(QFont("Segoe UI", 12, QFont.Bold))
        main_layout.addWidget(lbl_historial)

        self.table_movimientos = QTableWidget()
        self.table_movimientos.setColumnCount(7)
        self.table_movimientos.setHorizontalHeaderLabels(["Fecha", "Tipo", "Categoría", "Concepto", "Comprobante", "Monto", "Usuario"])
        self.table_movimientos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_movimientos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_movimientos.setAlternatingRowColors(True)
        self.table_movimientos.setContextMenuPolicy(Qt.CustomContextMenu)
        # Asignación del Tamaño de las Columnas de la Tabla
        for indice, ancho in enumerate((100, 70, 170, 370, 110, 120, 90), start=0):
            self.table_movimientos.setColumnWidth(indice, ancho)
        self.table_movimientos.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        main_layout.addWidget(self.table_movimientos)

        # --- Footer ---
        footer_layout = QHBoxLayout()
        self.btn_cierre = QPushButton("Cerrar Caja")
        self.btn_cierre.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        self.btn_cierre.clicked.connect(self.abrir_modal_cierre)
        footer_layout.addWidget(self.btn_cierre)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

    def create_dashboard_card(self, title, value, color):
        """Crea una tarjeta para el dashboard."""
        card = QFrame()
        card.setStyleSheet(f"background-color: {color}; border-radius: 8px; color: white;")
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
        if title == "Saldo Actual": self.lbl_saldo_val = lbl_value
        elif title == "Total Ingresos": self.lbl_ingresos_val = lbl_value
        elif title == "Total Egresos": self.lbl_egresos_val = lbl_value
        elif title == "Fondo Inicial": self.lbl_inicial_sesion_val = lbl_value
        return card

    def inicializar_sesion(self):
        """Busca una sesión abierta o crea una nueva."""
        try:
            query = "SELECT id FROM sesiones_caja WHERE caja_id = %s AND estado = 'Abierta' ORDER BY id DESC LIMIT 1"
            result = self.db.execute_query(query, (self.caja_id,))
            if result:
                self.sesion_id = result[0]['id']
            else:
                query_last = "SELECT monto_final_fisico FROM sesiones_caja WHERE caja_id = %s AND estado = 'Cerrada' ORDER BY fecha_cierre DESC LIMIT 1"
                last_session = self.db.execute_query(query_last, (self.caja_id,))
                monto_inicial = float(last_session[0]['monto_final_fisico']) if last_session else self.fondo_fijo
                query_insert = "INSERT INTO sesiones_caja (caja_id, usuario_id, fecha_apertura, monto_inicial, estado) VALUES (%s, %s, NOW(), %s, 'Abierta')"
                self.sesion_id = self.db.execute_query(query_insert, (self.caja_id, self.usuario_id, monto_inicial))
        except Exception as e:
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Error Crítico", f"No se pudo inicializar la sesión de caja: {e}")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            self.close()

    def load_initial_data(self):
        """Carga los datos iniciales de la UI."""
        self.actualizar_categorias()
        self.cargar_movimientos()

    def actualizar_categorias(self):
        """Actualiza el combobox de categorías según el tipo de movimiento."""
        tipo = self.cb_tipo_mov.currentText()
        query = "SELECT id, nombre FROM categorias_movimiento WHERE tipo = %s ORDER BY nombre"
        categorias = self.db.execute_query(query, (tipo,))
        self.cb_categoria.clear()
        if categorias:
            for cat in categorias:
                self.cb_categoria.addItem(cat['nombre'], userData=cat['id'])

    def cargar_movimientos(self):
        """Carga los movimientos de la sesión actual en la tabla."""
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, 
                   m.comprobante_tipo, m.comprobante_numero, m.monto, u.username
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            JOIN usuarios u ON m.usuario_id = u.id
            WHERE m.sesion_id = %s
            ORDER BY m.fecha_hora DESC, m.id DESC
        """
        movimientos = self.db.execute_query(query, (self.sesion_id,)) or []
        self.table_movimientos.setRowCount(len(movimientos))
        for row, mov in enumerate(movimientos):
            item_fecha = QTableWidgetItem(mov['fecha_hora'].strftime('%Y-%m-%d %H:%M'))
            item_fecha.setData(Qt.UserRole, mov['id']) # Guardamos el ID del movimiento
            self.table_movimientos.setItem(row, 0, item_fecha)
            self.table_movimientos.item(row, 0).setTextAlignment(Qt.AlignCenter)
            self.table_movimientos.setItem(row, 1, QTableWidgetItem(mov['tipo']))
            self.table_movimientos.item(row, 1).setTextAlignment(Qt.AlignCenter)
            self.table_movimientos.setItem(row, 2, QTableWidgetItem(mov['categoria']))
            self.table_movimientos.setItem(row, 3, QTableWidgetItem(mov['concepto']))
            comprob_tipo = mov.get('comprobante_tipo') or ''
            comprob_num = mov.get('comprobante_numero') or ''
            comprobante_full = f"{comprob_tipo}{comprob_num}"
            self.table_movimientos.setItem(row, 4, QTableWidgetItem(comprobante_full))
            self.table_movimientos.setItem(row, 5, QTableWidgetItem(self.format_money(mov['monto'])))
            self.table_movimientos.item(row, 5).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_movimientos.setItem(row, 6, QTableWidgetItem(mov['username']))
        self.calcular_totales()

    def calcular_totales(self):
        """Calcula y actualiza los totales del dashboard."""
        query_monto_inicial = "SELECT monto_inicial FROM sesiones_caja WHERE id = %s"
        res_inicial = self.db.execute_query(query_monto_inicial, (self.sesion_id,))
        monto_inicial_sesion = float(res_inicial[0]['monto_inicial']) if res_inicial else 0.0
        
        query_ingresos = "SELECT COALESCE(SUM(monto), 0) as total FROM movimientos_caja WHERE tipo = 'Ingreso' AND sesion_id = %s AND anulado = FALSE"
        res_ing = self.db.execute_query(query_ingresos, (self.sesion_id,))
        total_ingresos = float(res_ing[0]['total']) if res_ing else 0.0
        
        query_egresos = "SELECT COALESCE(SUM(monto), 0) as total FROM movimientos_caja WHERE tipo = 'Egreso' AND sesion_id = %s AND anulado = FALSE"
        res_egr = self.db.execute_query(query_egresos, (self.sesion_id,))
        total_egresos = float(res_egr[0]['total']) if res_egr else 0.0
        
        self.saldo_actual_caja = monto_inicial_sesion + total_ingresos - total_egresos
        
        self.lbl_inicial_sesion_val.setText(self.format_money(monto_inicial_sesion))
        self.lbl_ingresos_val.setText(self.format_money(total_ingresos))
        self.lbl_egresos_val.setText(self.format_money(total_egresos))
        self.lbl_saldo_val.setText(self.format_money(self.saldo_actual_caja))

    def guardar_movimiento(self):
        """Guarda un nuevo movimiento en la base de datos."""
        if not self.sesion_id: return
        
        tipo = self.cb_tipo_mov.currentText()
        categoria_id = self.cb_categoria.currentData()
        concepto = self.le_descripcion.text().strip()
        monto_str = self.le_monto.text().strip()
        
        comprobante_full = self.le_comprobante.text().strip()
        comprob_tipo = ''
        comprob_num = ''
        if comprobante_full:
            comprob_tipo = comprobante_full[0].upper()
            comprob_num = comprobante_full[1:9] # Limitar a 8 caracteres
        
        if not all([tipo, categoria_id, concepto, monto_str]):
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Campos Incompletos", "Los campos Tipo, Categoría, Concepto y Monto son obligatorios.")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0: raise ValueError()
        except ValueError:
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Monto Inválido", "Por favor, ingrese un monto válido y mayor a 0.")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            return

        if tipo == 'Egreso' and monto > self.saldo_actual_caja:
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Saldo Insuficiente", f"No puede registrar un egreso de {self.format_money(monto)} con un saldo de {self.format_money(self.saldo_actual_caja)}.")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            return

        try:
            query = """
                INSERT INTO movimientos_caja (sesion_id, usuario_id, caja_id, categoria_id, tipo, concepto, 
                                             comprobante_tipo, comprobante_numero, monto, fecha_hora)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = (self.sesion_id, self.usuario_id, self.caja_id, categoria_id, tipo, concepto, 
                      comprob_tipo, comprob_num, monto)
            
            nuevo_mov_id = self.db.execute_query(query, params)
            
            if nuevo_mov_id is not None:
                self.limpiar_form_movimiento()
                self.cargar_movimientos()
                # Generar el vale automáticamente después de guardar
                self._generar_vale_pdf(nuevo_mov_id, abrir_archivo=False)
            else:
                msg_box = QMessageBox(QMessageBox.Icon.Critical, "Error de Base de Datos", "No se pudo guardar el movimiento.")
                msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
                msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Error de Base de Datos", f"No se pudo guardar el movimiento: {e}")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()

    def limpiar_form_movimiento(self):
        """Limpia los campos del formulario de registro de movimientos."""
        self.le_descripcion.clear()
        self.le_monto.clear()
        self.le_comprobante.clear()
        self.le_descripcion.setFocus()

    def mostrar_menu_contextual(self, position):
        """Muestra el menú contextual en la tabla de movimientos."""
        selected_items = self.table_movimientos.selectedItems()
        if not selected_items: return
        menu = QMenu()
        
        action_eliminar = QAction("Eliminar Movimiento", self)
        action_eliminar.triggered.connect(self.eliminar_movimiento)
        
        menu.addAction(action_eliminar)
        
        menu.exec(self.table_movimientos.viewport().mapToGlobal(position))

    def eliminar_movimiento(self):
        """Elimina físicamente el movimiento seleccionado de la base de datos."""
        selected = self.table_movimientos.selectedItems()
        if not selected: return
        
        row = selected[0].row()
        mov_id = self.table_movimientos.item(row, 0).data(Qt.UserRole)
        concepto = self.table_movimientos.item(row, 3).text()
        
        msg_box = QMessageBox(QMessageBox.Icon.Question, "Confirmar Eliminación", 
                              f"¿Está seguro de eliminar permanentemente el movimiento?\n\nID: {mov_id}\nConcepto: {concepto}",
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        msg_box.button(QMessageBox.StandardButton.Yes).setText("Sí")
        msg_box.button(QMessageBox.StandardButton.No).setText("No")
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM movimientos_caja WHERE id = %s"
                self.db.execute_query(query, (mov_id,))
                logging.info(f"[MAIN_WINDOW] Movimiento ID {mov_id} eliminado.")
                self.cargar_movimientos()
            except Exception as e:
                msg_err = QMessageBox(QMessageBox.Icon.Critical, "Error", f"No se pudo eliminar el movimiento: {e}")
                msg_err.addButton("Aceptar", QMessageBox.AcceptRole)
                msg_err.exec()

    def _generar_vale_pdf(self, mov_id, abrir_archivo=False):
        """
        Lógica centralizada para generar el PDF de un vale.
        :param mov_id: ID del movimiento a imprimir.
        :param abrir_archivo: Si es True, abre el archivo después de crearlo.
        """
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, m.monto,
                   m.comprobante_tipo, m.comprobante_numero
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
                #parametros = {'simbolo_moneda': self.simbolo_moneda}
                parametros = {
                    'simbolo_moneda': self.simbolo_moneda,
                    'nombre_empresa': self.nombre_empresa,
                    'ruta_logo': self.ruta_logo
                }
                generar_vale_pdf(mov_data, filepath, parametros=parametros)
                logging.info(f"[MAIN_WINDOW] Vale generado para movimiento ID {mov_id} en {filepath}.")
                if abrir_archivo:
                    os.startfile(filepath)
            except Exception as e:
                logging.error(f"[MAIN_WINDOW] Error al generar vale PDF para mov ID {mov_id}: {e}")
                # No mostramos un pop-up aquí para no interrumpir el flujo de guardado automático
                if abrir_archivo:
                    msg_err = QMessageBox(QMessageBox.Icon.Critical, "Error", f"Error generando o abriendo PDF: {e}")
                    msg_err.addButton("Aceptar", QMessageBox.AcceptRole)
                    msg_err.exec()

    def mostrar_dialogo_reporte(self):
        """Muestra el diálogo para solicitar el rango de fechas del reporte general."""
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
        """Genera el reporte general basado en el rango de fechas seleccionado."""
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
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Sin Datos", "No se encontraron movimientos en el rango de fechas seleccionado.")
                msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
                msg_box.exec()
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
            #parametros = {'simbolo_moneda': self.simbolo_moneda}
            parametros = {
                'simbolo_moneda': self.simbolo_moneda,
                'nombre_empresa': self.nombre_empresa,
                'ruta_logo': self.ruta_logo
            }
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
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Error", f"No se pudo generar el reporte: {e}")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            logging.error(f"[MAIN_WINDOW] Error al generar reporte: {e}", exc_info=True)

    def mostrar_dialogo_reporte_categoria(self):
        """Muestra el diálogo para generar el reporte por categoría."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Reporte por Categoría y Fecha")
        layout = QFormLayout(dialog)

        start_date_edit = QDateEdit(QDate.currentDate().addDays(-30))
        start_date_edit.setCalendarPopup(True)
        end_date_edit = QDateEdit(QDate.currentDate())
        end_date_edit.setCalendarPopup(True)

        cat_from_combo = QComboBox()
        cat_to_combo = QComboBox()
        
        categorias = self.db.execute_query("SELECT id, nombre FROM categorias_movimiento ORDER BY nombre")
        if categorias:
            cat_from_combo.addItem("Todas", userData=None)
            cat_to_combo.addItem("Todas", userData=None)
            for cat in categorias:
                cat_from_combo.addItem(cat['nombre'], userData=cat['id'])
                cat_to_combo.addItem(cat['nombre'], userData=cat['id'])

        layout.addRow("Fecha de Inicio:", start_date_edit)
        layout.addRow("Fecha de Fin:", end_date_edit)
        layout.addRow("Categoría Desde:", cat_from_combo)
        layout.addRow("Categoría Hasta:", cat_to_combo)

        btn_generar = QPushButton("Generar PDF")
        btn_generar.clicked.connect(lambda: self.generar_reporte_categoria(
            dialog, start_date_edit.date(), end_date_edit.date(),
            cat_from_combo.currentData(), cat_to_combo.currentData()
        ))
        layout.addRow(btn_generar)
        
        dialog.exec()

    def generar_reporte_categoria(self, dialog, start_date, end_date, cat_from_id, cat_to_id):
        """Genera y abre el reporte de movimientos por categoría."""
        start_date_str = start_date.toString("yyyy-MM-dd")
        end_date_str = end_date.toString("yyyy-MM-dd")

        if start_date > end_date:
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Error de Fechas", "La fecha de inicio no puede ser posterior a la fecha de fin.")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            return

        query = """
            SELECT m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, 
                   m.comprobante_tipo, m.comprobante_numero, m.monto
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            WHERE DATE(m.fecha_hora) BETWEEN %s AND %s
        """
        params = [start_date_str, end_date_str]

        if cat_from_id is not None and cat_to_id is not None:
            if cat_from_id > cat_to_id:
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Error de Categorías", "La categoría 'Desde' no puede ser posterior a la categoría 'Hasta'.")
                msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
                msg_box.exec()
                return
            query += " AND c.id BETWEEN %s AND %s"
            params.extend([cat_from_id, cat_to_id])
        
        query += " ORDER BY c.nombre, m.fecha_hora"
        
        movimientos = self.db.execute_query(query, tuple(params))

        if not movimientos:
            msg_box = QMessageBox(QMessageBox.Icon.Information, "Sin Datos", "No se encontraron movimientos para los filtros seleccionados.")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()
            return

        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"reporte_por_categoria_{start_date_str}_a_{end_date_str}.pdf"
        filepath = os.path.join(reports_dir, filename)

        info_extra = {
            'desde': start_date.toString("dd/MM/yyyy"),
            'hasta': end_date.toString("dd/MM/yyyy"),
            'caja_nombre': self.caja_nombre
        }
        #parametros = {'simbolo_moneda': self.simbolo_moneda}
        parametros = {
            'simbolo_moneda': self.simbolo_moneda,
            'nombre_empresa': self.nombre_empresa,
            'ruta_logo': self.ruta_logo
        }

        try:
            generar_reporte_por_categoria(movimientos, info_extra, filepath, parametros)
            os.startfile(filepath)
            dialog.accept()
        except Exception as e:
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Error", f"No se pudo generar el reporte: {e}")
            msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
            msg_box.exec()

    def abrir_report_viewer(self):
        #dialog = ReportViewerWindow(self.rol, self.caja_nombre, self)
        dialog = ReportViewerWindow(self.rol, self.caja_nombre, self.db, self)
        dialog.exec()
    def abrir_crud_empresa(self):
        dialog = CrudEmpresa(self.db, self)
        dialog.exec()
    def abrir_crud_usuarios(self):
        dialog = CrudUsuarios(self.db, self)
        dialog.exec()
    def abrir_crud_cajas(self):
        dialog = CrudCajas(self.db, self)
        dialog.exec()
    def abrir_crud_categorias(self):
        dialog = CrudCategorias(self.db, self)
        dialog.exec()
    def abrir_modal_cierre(self):
        dialog = ModalCierre(self.db, self.sesion_id, self.simbolo_moneda, self.caja_nombre, self.username, self)
        if dialog.exec() == QDialog.Accepted:
            self.close()
    def closeEvent(self, event):
        super().closeEvent(event)
