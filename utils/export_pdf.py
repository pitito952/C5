from fpdf import FPDF
import os
import datetime

class PDFReport(FPDF):
    def __init__(self, parametros=None, **kwargs):
        super().__init__(**kwargs)
        self.parametros = parametros or {}

    def header(self):
        # Logo
        logo_path = self.parametros.get('ruta_logo')
        if logo_path and os.path.isfile(logo_path):
            try:
                self.image(logo_path, 10, 8, 33)
            except Exception:
                pass 
        
        self.set_font("Arial", "B", 15)
        
        if logo_path and os.path.isfile(logo_path):
            self.cell(40)
            
        nombre_empresa = self.parametros.get('nombre_empresa', 'Reporte de Caja Chica')
        self.cell(0, 10, nombre_empresa, 0, 1, "C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

def generar_vale_pdf(movimiento_data, output_path="vale.pdf", parametros=None):
    # Obtener símbolo de moneda de los parámetros, por defecto '$'
    simbolo = parametros.get('simbolo_moneda', '$') if parametros else '$'
    
    pdf = PDFReport(parametros=parametros)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 14)
    tipo = movimiento_data['tipo'].upper()
    pdf.cell(0, 10, f"COMPROBANTE DE {tipo}", 0, 1, "C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(50, 10, "Nro. de Registro:", 0, 0)
    pdf.cell(0, 10, str(movimiento_data['id']), 0, 1)
    
    pdf.cell(50, 10, "Fecha y Hora:", 0, 0)
    fecha = movimiento_data['fecha_hora']
    if isinstance(fecha, datetime.datetime):
        fecha = fecha.strftime('%d/%m/%Y %H:%M')
    pdf.cell(0, 10, str(fecha), 0, 1)
    
    pdf.cell(50, 10, "Categoría:", 0, 0)
    pdf.cell(0, 10, str(movimiento_data['categoria']), 0, 1)
    
    pdf.cell(50, 10, "Concepto:", 0, 0)
    pdf.cell(0, 10, str(movimiento_data['concepto']), 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(50, 10, "MONTO:", 0, 0)
    pdf.cell(0, 10, f"{simbolo} {float(movimiento_data['monto']):.2f}", 0, 1)
    
    pdf.ln(20)
    pdf.set_font("Arial", "", 12)
    pdf.cell(90, 10, "_________________________")
    pdf.cell(90, 10, "_________________________")
    pdf.ln(8)
    pdf.cell(90, 10, "Firma Entregado por")
    pdf.cell(90, 10, "Firma Recibido por")
    
    pdf.output(output_path)
    return output_path

def generar_listado_pdf(movimientos_list, info_extra, parametros=None, output_path="reporte_movimientos.pdf"):
    simbolo = parametros.get('simbolo_moneda', '$') if parametros else '$'
    
    pdf = PDFReport(parametros=parametros, orientation='landscape')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Listado de Movimientos", 0, 1, "C")
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Filtrado desde: {info_extra['desde']} hasta: {info_extra['hasta']}", 0, 1)
    pdf.cell(0, 8, f"Emitido por Usuario: {info_extra['usuario']}", 0, 1)
    pdf.ln(5)
    
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 9)
    
    w = [30, 35, 30, 15, 35, 105, 27]
    
    headers = ["Fecha", "Caja", "Usuario", "Tipo", "Categoría", "Concepto", f"Monto ({simbolo})"]
    for i in range(7):
        pdf.cell(w[i], 8, headers[i], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    total_ingresos = 0.0
    total_egresos = 0.0
    
    for row in movimientos_list:
        fecha = row['fecha_hora']
        if isinstance(fecha, datetime.datetime):
            fecha = fecha.strftime('%d/%m/%Y %H:%M')
            
        monto = float(row['monto'])
        if row['tipo'] == 'Ingreso':
            total_ingresos += monto
        else:
            total_egresos += monto
            
        concepto = str(row['concepto'])[:60]
        caja_name = str(row.get('caja', 'N/A'))[:20]
        usuario_name = str(row.get('usuario', 'N/A'))[:15]
        
        pdf.cell(w[0], 6, str(fecha), 1)
        pdf.cell(w[1], 6, caja_name, 1)
        pdf.cell(w[2], 6, usuario_name, 1)
        pdf.cell(w[3], 6, str(row['tipo']), 1)
        pdf.cell(w[4], 6, str(row.get('categoria', ''))[:20], 1)
        pdf.cell(w[5], 6, concepto, 1)
        
        pdf.cell(w[6], 6, f"{monto:.2f}", 1, 0, 'R')
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"TOTAL INGRESOS: {simbolo} {total_ingresos:.2f}", 0, 1, 'R')
    pdf.cell(0, 8, f"TOTAL EGRESOS: {simbolo} {total_egresos:.2f}", 0, 1, 'R')
    pdf.cell(0, 8, f"SALDO PERIODO: {simbolo} {(total_ingresos - total_egresos):.2f}", 0, 1, 'R')

    pdf.output(output_path)
    return output_path

def generar_reporte_cierre(cierre_data, output_path="cierre.pdf", parametros=None):
    simbolo = parametros.get('simbolo_moneda', '$') if parametros else '$'
    
    pdf = PDFReport(parametros=parametros)
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Comprobante de Cierre de Caja", 0, 1, "C")
    pdf.ln(10)
    
    # Info General
    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 8, "Fecha de Cierre:", 0, 0)
    pdf.cell(0, 8, cierre_data['fecha_cierre'], 0, 1)
    pdf.cell(40, 8, "Caja:", 0, 0)
    pdf.cell(0, 8, cierre_data['caja_nombre'], 0, 1)
    pdf.cell(40, 8, "Usuario:", 0, 0)
    pdf.cell(0, 8, cierre_data['usuario_nombre'], 0, 1)
    pdf.ln(5)
    
    # Resumen Financiero
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumen Financiero de la Sesión", 0, 1)
    pdf.set_font("Arial", "", 11)
    
    # Usar un ancho fijo para las etiquetas para alinear los valores
    label_w = 60
    value_w = 40

    pdf.cell(label_w, 8, "Monto Inicial:", 0, 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['monto_inicial']:.2f}", 0, 1, 'R')
    
    pdf.cell(label_w, 8, "Total Ingresos (+):", 0, 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['total_ingresos']:.2f}", 0, 1, 'R')
    
    pdf.cell(label_w, 8, "Total Egresos (-):", 0, 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['total_egresos']:.2f}", 0, 1, 'R')
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(label_w, 8, "Saldo del Sistema:", 'T', 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['saldo_sistema']:.2f}", 'T', 1, 'R')
    pdf.ln(5)
    
    # Arqueo
    pdf.set_font("Arial", "", 11)
    pdf.cell(label_w, 8, "Efectivo Contado:", 0, 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['monto_fisico']:.2f}", 0, 1, 'R')
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(label_w, 8, "Diferencia:", 'T', 0)
    pdf.cell(value_w, 8, f"{simbolo} {cierre_data['diferencia']:.2f}", 'T', 1, 'R')
    pdf.ln(5)
    
    # Observaciones
    if cierre_data['observaciones']:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Observaciones", 0, 1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, cierre_data['observaciones'], 1, 'L')
        pdf.ln(10)
        
    # Firmas
    pdf.ln(20)
    pdf.set_font("Arial", "", 12)
    pdf.cell(90, 10, "_________________________")
    pdf.cell(90, 10, "_________________________")
    pdf.ln(8)
    pdf.cell(90, 10, "Firma del Cajero")
    pdf.cell(90, 10, "Firma del Supervisor")

    pdf.output(output_path)
    return output_path
