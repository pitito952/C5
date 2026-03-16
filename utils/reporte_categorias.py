from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.simbolo_moneda = ""

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, 'Reporte de Movimientos por Categoría', 0, 0, 'L')
        self.set_font('Arial', '', 8)
        self.cell(0, 5, f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, data):
        self.set_font('Arial', 'B', 9)
        self.cell(25, 7, 'Fecha', 1, 0, 'C')
        self.cell(70, 7, 'Concepto', 1, 0, 'C')
        self.cell(65, 7, 'Comprobante', 1, 0, 'C')
        self.cell(30, 7, 'Monto', 1, 1, 'C')

        self.set_font('Arial', '', 9)
        total_categoria = 0
        for row in data:
            self.cell(25, 7, row['fecha_hora'].strftime('%d-%m-%Y'), 1)
            self.cell(70, 7, str(row.get('concepto') or ''), 1)
            
            comprob_tipo = row.get('comprobante_tipo') or ''
            comprob_num = row.get('comprobante_numero') or ''
            comprobante_full = f"{comprob_tipo}{comprob_num}"
            self.cell(65, 7, comprobante_full, 1)
            
            monto = float(row.get('monto', 0))
            self.cell(30, 7, f"{self.simbolo_moneda} {monto:,.2f}", 1, 1, 'R')
            total_categoria += monto
        
        self.set_font('Arial', 'B', 9)
        self.cell(160, 7, 'Total por Categoría:', 1, 0, 'R')
        self.cell(30, 7, f"{self.simbolo_moneda} {total_categoria:,.2f}", 1, 1, 'R')
        self.ln(10)

def generar_reporte_por_categoria(movimientos, info_extra, output_path, parametros):
    pdf = PDF('P', 'mm', 'A4')
    pdf.simbolo_moneda = parametros.get('simbolo_moneda', '$')
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, f"Rango de Fechas: {info_extra['desde']} al {info_extra['hasta']}", 0, 1)
    pdf.cell(0, 7, f"Caja: {info_extra['caja_nombre']}", 0, 1)
    pdf.ln(5)

    total_ingresos = 0
    total_egresos = 0
    
    mov_por_categoria = {}
    for mov in movimientos:
        categoria = mov['categoria']
        if categoria not in mov_por_categoria:
            mov_por_categoria[categoria] = []
        mov_por_categoria[categoria].append(mov)
        
        if mov['tipo'] == 'Ingreso':
            total_ingresos += float(mov.get('monto', 0))
        else:
            total_egresos += float(mov.get('monto', 0))

    for categoria, movs in sorted(mov_por_categoria.items()):
        pdf.chapter_title(f"Categoría: {categoria}")
        pdf.chapter_body(movs)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Resumen General', 0, 1, 'L')
    pdf.set_font('Arial', 'B', 10)
    
    pdf.cell(160, 8, 'Total Ingresos:', 1, 0, 'R')
    pdf.cell(30, 8, f"{pdf.simbolo_moneda} {total_ingresos:,.2f}", 1, 1, 'R')
    
    pdf.cell(160, 8, 'Total Egresos:', 1, 0, 'R')
    pdf.cell(30, 8, f"{pdf.simbolo_moneda} {total_egresos:,.2f}", 1, 1, 'R')
    
    saldo_neto = total_ingresos - total_egresos
    pdf.cell(160, 8, 'Saldo Neto del Período:', 1, 0, 'R')
    pdf.cell(30, 8, f"{pdf.simbolo_moneda} {saldo_neto:,.2f}", 1, 1, 'R')

    pdf.output(output_path)
