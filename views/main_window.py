from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QAbstractItemView, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction
from database.connection import DatabaseConnection
from views.modal_movimiento import ModalMovimiento
from views.modal_cierre import ModalCierre
from views.modal_reporte import ModalReporte
from views.crud_usuarios import CrudUsuarios
from views.crud_cajas import CrudCajas
from views.crud_categorias import CrudCategorias
from views.crud_empresa import CrudEmpresa
from utils.export_pdf import generar_vale_pdf
import os

class MainWindow(QMainWindow):
    def __init__(self, usuario_id, username, rol, caja_id, caja_nombre):
        super().__init__()
        self.usuario_id = usuario_id
        self.username = username
        self.rol = rol
        self.caja_id = caja_id
        self.caja_nombre = caja_nombre
        
        self.setWindowTitle(f"Módulo de Caja Chica - Bienvenido(a): {self.username} ({self.rol}) | Caja: {self.caja_nombre}")
        self.resize(1000, 600)
        
        self.setup_menu_bar()

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.db = DatabaseConnection()
        
        self.setup_header()
        self.setup_dashboard()
        self.setup_table()
        self.setup_footer_actions()
        
        self.load_data_from_db()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        # Menu changes depending on role
        if self.rol == 'Administrador':
            menu_admin = menubar.addMenu("⚡ Administración")
            
            act_usuarios = QAction("Gestión de Usuarios", self)
            act_usuarios.triggered.connect(self.abrir_crud_usuarios)
            menu_admin.addAction(act_usuarios)
            
            act_cajas = QAction("Gestión de Cajas", self)
            act_cajas.triggered.connect(self.abrir_crud_cajas)
            menu_admin.addAction(act_cajas)
            
            act_categorias = QAction("Categorías de Movimiento", self)
            act_categorias.triggered.connect(self.abrir_crud_categorias)
            menu_admin.addAction(act_categorias)
            
            act_empresa = QAction("Configuración de Empresa", self)
            act_empresa.triggered.connect(self.abrir_crud_empresa)
            menu_admin.addAction(act_empresa)
            

    def setup_header(self):
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Gestión de Caja Chica")
        font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(font)
        
        self.status_label = QLabel("Estado: Abierta | Sesión #1")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.btn_reporte = QPushButton("📄 Generar Reporte PDF")
        self.btn_reporte.setStyleSheet("background-color: #6f42c1; color: white; padding: 5px;")
        self.btn_reporte.clicked.connect(self.abrir_reporte)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_reporte)
        header_layout.addWidget(self.status_label)

        self.main_layout.addLayout(header_layout)

    def setup_dashboard(self):
        dash_frame = QFrame()
        dash_frame.setFrameShape(QFrame.StyledPanel)
        dash_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QLabel { border: none; }
        """)
        dash_layout = QHBoxLayout(dash_frame)
        
        # Labels for balances
        self.lbl_initial = self.create_metric_card("Fondo / Inicial:", "$ 1,000.00")
        self.lbl_in = self.create_metric_card("Ingresos:", "$ 150.00", color="green")
        self.lbl_out = self.create_metric_card("Egresos:", "$ 320.00", color="red")
        
        # Net balance
        saldo_layout = QVBoxLayout()
        lbl_saldo_title = QLabel("Saldo Actual")
        lbl_saldo_title.setAlignment(Qt.AlignCenter)
        self.lbl_saldo_val = QLabel("$ 830.00")
        self.lbl_saldo_val.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_saldo_val.setStyleSheet("color: #0d6efd;")
        self.lbl_saldo_val.setAlignment(Qt.AlignCenter)
        saldo_layout.addWidget(lbl_saldo_title)
        saldo_layout.addWidget(self.lbl_saldo_val)

        dash_layout.addLayout(self.lbl_initial)
        dash_layout.addLayout(self.lbl_in)
        dash_layout.addLayout(self.lbl_out)
        dash_layout.addStretch()
        dash_layout.addLayout(saldo_layout)

        self.main_layout.addWidget(dash_frame)

    def create_metric_card(self, title, value, color="black"):
        layout = QVBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6c757d; font-size: 12px;")
        
        lbl_val = QLabel(value)
        lbl_val.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color};")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return layout

    def setup_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Fecha/Hora", "Tipo", "Categoría", "Concepto", "Comprobante", "Monto"
        ])
        
        # Table properties
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        for indice, ancho in enumerate((100, 60, 200, 200, 110, 130), start=0):
            self.table.setColumnWidth(indice, ancho)
        
        # Set default row height
        self.table.verticalHeader().setDefaultSectionSize(18)

        self.table.setStyleSheet("QTableWidget { border: none; \
                                                font: 10pt 'Noto Sans'; \
                                              } \
                                 QHeaderView::section {	border: none; \
                                                        font: 10pt 'Noto Sans'; \
                                                        background-color: rgb(218, 255, 197); \
                                                        color: rgb(0, 0, 0); \
                                                      }")
        
        # Enable context menu for right clicks
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Tooltip for user guidance
        self.table.setToolTip("Haz clic derecho sobre un registro para Anularlo o Imprimir su Comprobante.")
        
        # Stretch columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch) # Concepto occupies extra space

        self.main_layout.addWidget(self.table)

    def setup_footer_actions(self):
        action_layout = QHBoxLayout()
        
        self.btn_ingreso = QPushButton("+ Nuevo Ingreso")
        self.btn_ingreso.setMinimumHeight(35)
        self.btn_ingreso.setStyleSheet("background-color: #198754; color: white; font-weight: bold; border-radius: 5px; padding-left: 8px; padding-right: 8px;")
        
        self.btn_egreso = QPushButton("- Nuevo Egreso")
        self.btn_egreso.setMinimumHeight(35)
        self.btn_egreso.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 5px; padding-left: 8px; padding-right: 8px;")
        
        self.btn_cierre = QPushButton("Cerrar Caja")
        self.btn_cierre.setMinimumHeight(35)
        self.btn_cierre.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold; border-radius: 5px; padding-left: 8px; padding-right: 8px;")

        # Connect actions
        self.btn_ingreso.clicked.connect(self.abrir_ingreso)
        self.btn_egreso.clicked.connect(self.abrir_egreso)
        self.btn_cierre.clicked.connect(self.abrir_cierre)

        action_layout.addWidget(self.btn_ingreso)
        action_layout.addWidget(self.btn_egreso)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_cierre)

        self.main_layout.addLayout(action_layout)

    def load_data_from_db(self):
        # 1. Fetch active session
        query_session = "SELECT * FROM sesiones_caja WHERE estado = 'Abierta' ORDER BY id DESC LIMIT 1"
        session = self.db.execute_query(query_session)
        
        if not session:
            self.status_label.setText("Estado: Cerrada | No hay sesión activa")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.lbl_initial.itemAt(1).widget().setText("$ 0.00")
            self.lbl_in.itemAt(1).widget().setText("$ 0.00")
            self.lbl_out.itemAt(1).widget().setText("$ 0.00")
            self.lbl_saldo_val.setText("$ 0.00")
            return
            
        active_session = session[0]
        sesion_id = active_session['id']
        monto_inicial = active_session['monto_inicial']
        
        self.status_label.setText(f"Estado: Abierta | Sesión #{sesion_id}")
        
        # 2. Fetch movements for this session (only NON-annulled)
        query_movs = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, 
                   IFNULL(m.comprobante_numero, 'N/A') as comprobante, m.monto
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            WHERE m.sesion_id = %s AND m.anulado = FALSE
            ORDER BY m.fecha_hora DESC
        """
        movs = self.db.execute_query(query_movs, (sesion_id,)) or []
        
        # 3. Calculate totals and populate table
        total_in = 0.0
        total_out = 0.0
        
        self.table.setRowCount(len(movs))
        
        for row_idx, row_data in enumerate(movs):
            fecha = row_data['fecha_hora'].strftime("%d/%m/%Y %H:%M")
            tipo = row_data['tipo']
            monto_val = float(row_data['monto'])
            mov_id = row_data['id']
            
            if tipo == 'Ingreso':
                total_in += monto_val
                monto_str = f"{monto_val:.2f}"
            else:
                total_out += monto_val
                monto_str = f"-{monto_val:.2f}"
                
            display_row = (
                fecha,
                tipo,
                row_data['categoria'],
                row_data['concepto'],
                row_data['comprobante'],
                monto_str
            )

            for col_idx, value in enumerate(display_row):
                item = QTableWidgetItem(str(value))
                if col_idx == 0:
                    # Guardamos el ID del movimiento en la primera columna para usarlo luego
                    item.setData(Qt.UserRole, mov_id)
                elif col_idx == 5:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if str(value).startswith("-"):
                        item.setForeground(Qt.red)
                    else:
                        item.setForeground(Qt.darkGreen)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)

        # Update dashboard numbers
        saldo_actual = float(monto_inicial) + total_in - total_out
        
        self.lbl_initial.itemAt(1).widget().setText(f"$ {float(monto_inicial):.2f}")
        self.lbl_in.itemAt(1).widget().setText(f"$ {total_in:.2f}")
        self.lbl_out.itemAt(1).widget().setText(f"$ {total_out:.2f}")
        self.lbl_saldo_val.setText(f"$ {saldo_actual:.2f}")

    def abrir_ingreso(self):
        # We need the active session ID to attach the movement
        query = "SELECT id FROM sesiones_caja WHERE estado = 'Abierta' AND caja_id = %s ORDER BY id DESC LIMIT 1"
        res = self.db.execute_query(query, (self.caja_id,))
        if not res:
            QMessageBox.warning(self, "Error", "Debe abrir una caja primero.")
            return
            
        modal = ModalMovimiento(self.db, res[0]['id'], "Ingreso", self.usuario_id, self.caja_id, parent=self)
        if modal.exec():
            self.load_data_from_db()

    def abrir_egreso(self):
        query = "SELECT id FROM sesiones_caja WHERE estado = 'Abierta' AND caja_id = %s ORDER BY id DESC LIMIT 1"
        res = self.db.execute_query(query, (self.caja_id,))
        if not res:
            QMessageBox.warning(self, "Error", "Debe abrir una caja primero.")
            return
            
        modal = ModalMovimiento(self.db, res[0]['id'], "Egreso", self.usuario_id, self.caja_id, parent=self)
        if modal.exec():
            self.load_data_from_db()

    def abrir_cierre(self):
        query = "SELECT id FROM sesiones_caja WHERE estado = 'Abierta' ORDER BY id DESC LIMIT 1"
        res = self.db.execute_query(query)
        if not res:
            QMessageBox.warning(self, "Error", "No hay ninguna caja abierta para cerrar.")
            return
            
        modal = ModalCierre(self.db, res[0]['id'], parent=self)
        if modal.exec():
            self.load_data_from_db()

    def show_context_menu(self, pos):
        # Obtain row hovered
        item = self.table.itemAt(pos)
        if item is None:
            return
            
        row = item.row()
        menu = QMenu(self)
        
        action_anular = QAction("🚫 Eliminar / Anular Registro", self)
        action_anular.triggered.connect(lambda: self.anular_movimiento(row))
        menu.addAction(action_anular)
        
        action_imprimir = QAction("🖨️ Generar Comprobante (Vale en PDF)", self)
        action_imprimir.triggered.connect(lambda: self.imprimir_comprobante(row))
        menu.addAction(action_imprimir)
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
        
    def anular_movimiento(self, row):
        # We stored the db movement ID in the first column's UserRole
        mov_id = self.table.item(row, 0).data(Qt.UserRole)
        
        if not mov_id:
            return
            
        concepto = self.table.item(row, 3).text()
        monto = self.table.item(row, 5).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirmar Anulación", 
            f"¿Estás seguro que deseas ELIMINAR permanentemente este registro?\n\nDetalle: {concepto} ({monto})",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # We use logical deletion
                query = "UPDATE movimientos_caja SET anulado = TRUE WHERE id = %s"
                self.db.execute_query(query, (mov_id,))
                
                QMessageBox.information(self, "Eliminado", "Registro eliminado correctamente. Los saldos han sido recalculados.")
                
                # Refresh data
                self.load_data_from_db()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo anular el registro: {str(e)}")

    def imprimir_comprobante(self, row):
        mov_id = self.table.item(row, 0).data(Qt.UserRole)
        if not mov_id:
            return
            
        # Re-fetch full details to pass to the PDF generator since table lacks some internal IDs
        query = """
            SELECT m.id, m.fecha_hora, m.tipo, c.nombre as categoria, m.concepto, 
                   m.comprobante_numero as comprobante, m.monto
            FROM movimientos_caja m
            JOIN categorias_movimiento c ON m.categoria_id = c.id
            WHERE m.id = %s
        """
        res = self.db.execute_query(query, (mov_id,))
        if res:
            try:
                mov_data = res[0]
                pdf_target = os.path.join(os.getcwd(), f"comprobante_{mov_id}.pdf")
                
                parametros = {}
                try:
                    p_res = self.db.execute_query("SELECT * FROM parametros_control WHERE id = 1")
                    if p_res:
                        parametros = p_res[0]
                except Exception:
                    pass
                
                generar_vale_pdf(mov_data, pdf_target, parametros)
                QMessageBox.information(self, "PDF Generado", f"Vale guardado correctamente en:\n{pdf_target}")
                # Opcional: intentar abrirlo automáticamente
                os.startfile(pdf_target)
            except Exception as e:
                QMessageBox.critical(self, "Error PDF", f"Fallo al crear el PDF:\n{str(e)}")

    def abrir_reporte(self):
        user_info = {
            'id': self.usuario_id,
            'username': self.username,
            'rol': self.rol
        }
        modal = ModalReporte(self.db, user_info, parent=self)
        modal.exec()

    def abrir_crud_usuarios(self):
        crud = CrudUsuarios(self.db, parent=self)
        crud.exec()

    def abrir_crud_cajas(self):
        crud = CrudCajas(self.db, parent=self)
        crud.exec()

    def abrir_crud_categorias(self):
        crud = CrudCategorias(self.db, parent=self)
        crud.exec()

    def abrir_crud_empresa(self):
        crud = CrudEmpresa(self.db, parent=self)
        crud.exec()
