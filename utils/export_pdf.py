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
                pass # If image is unsupported or corrupted, skip it
        
        # Arial bold 15
        self.set_font("Arial", "B", 15)
        
        # If there's a logo, move text to the right
        if logo_path and os.path.isfile(logo_path):
            self.cell(40)
            
        # Title using company name if available
        nombre_empresa = self.parametros.get('nombre_empresa', 'Reporte de Caja Chica')
        self.cell(0, 10, nombre_empresa, 0, 1, "C")
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        # Page number
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

def generar_vale_pdf(movimiento_data, output_path="vale.pdf", parametros=None):
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
    
    comp_ref = movimiento_data.get('comprobante')
    if not comp_ref or str(comp_ref).strip() == '' or comp_ref == 'None':
        comp_ref = 'N/A'
    pdf.cell(50, 10, "Referencia Externa:", 0, 0)
    pdf.cell(0, 10, str(comp_ref), 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(50, 10, "MONTO:", 0, 0)
    pdf.cell(0, 10, f"$ {float(movimiento_data['monto']):.2f}", 0, 1)
    
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
    pdf = PDFReport(parametros=parametros, orientation='landscape')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Listado de Movimientos", 0, 1, "C")
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Filtrado desde: {info_extra['desde']} hasta: {info_extra['hasta']}", 0, 1)
    pdf.cell(0, 8, f"Emitido por Usuario: {info_extra['usuario']}", 0, 1)
    pdf.ln(5)
    
    # Headers - Landscape Width = 277 total printable horizontally
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 9)
    
    # Widths: Date(30), Caja(35), Usuario(30), Type(15), Category(35), Concept(105), Monto(27) = 277
    w = [30, 35, 30, 15, 35, 105, 27]
    
    headers = ["Fecha", "Caja", "Usuario", "Tipo", "Categoría", "Concepto", "Monto ($)"]
    for i in range(7):
        pdf.cell(w[i], 8, headers[i], 1, 0, 'C', True)
    pdf.ln()
    
    # Data Rows
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
            
        # Truncate text to avoid lines spilling in strict tabular layout.
        # FPDF has wordwrap, but simple cell() pushes text out of bounds.
        concepto = str(row['concepto'])[:60]
        caja_name = str(row.get('caja', 'N/A'))[:20]
        usuario_name = str(row.get('usuario', 'N/A'))[:15]
        
        pdf.cell(w[0], 6, str(fecha), 1)
        pdf.cell(w[1], 6, caja_name, 1)
        pdf.cell(w[2], 6, usuario_name, 1)
        pdf.cell(w[3], 6, str(row['tipo']), 1)
        pdf.cell(w[4], 6, str(row.get('categoria', ''))[:20], 1)
        pdf.cell(w[5], 6, concepto, 1)
        
        # Right align montos
        pdf.cell(w[6], 6, f"{monto:.2f}", 1, 0, 'R')
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"TOTAL INGRESOS: $ {total_ingresos:.2f}", 0, 1, 'R')
    pdf.cell(0, 8, f"TOTAL EGRESOS: $ {total_egresos:.2f}", 0, 1, 'R')
    pdf.cell(0, 8, f"SALDO PERIODO: $ {(total_ingresos - total_egresos):.2f}", 0, 1, 'R')

    pdf.output(output_path)
    return output_path
