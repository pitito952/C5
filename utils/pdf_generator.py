# *****************************************************************************
#   Sistema:    C5    -   Módulo de Caja Chica
#   Archivo:    utils/pdf_generator.py
#   Descripción: Generador de reportes PDF para Cierres de Caja
# *****************************************************************************

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

class PDFGenerator:
    def __init__(self, output_dir="reports"):
        """
        Inicializa el generador de PDF.
        :param output_dir: Directorio donde se guardarán los PDFs.
        """
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generar_reporte_cierre(self, datos_cierre):
        """
        Genera un PDF con el resumen del cierre de caja.
        
        :param datos_cierre: Diccionario con la siguiente estructura:
            {
                'sesion_id': int,
                'usuario': str,
                'caja': str,
                'fecha_inicio': str,
                'fecha_cierre': str,
                'saldo_inicial': float,
                'total_ingresos': float,
                'total_egresos': float,
                'saldo_calculado': float,
                'saldo_real': float,
                'diferencia': float,
                'observaciones': str
            }
        :return: Ruta absoluta del archivo generado.
        """
        # Nombre del archivo basado en fecha y caja
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Cierre_{datos_cierre['caja']}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # --- Estilos Personalizados ---
        title_style = ParagraphStyle(
            'TitleCustom', 
            parent=styles['Heading1'], 
            alignment=TA_CENTER,
            spaceAfter=20
        )
        normal_center = ParagraphStyle(
            'NormalCenter',
            parent=styles['Normal'],
            alignment=TA_CENTER
        )

        # --- Encabezado ---
        elements.append(Paragraph("REPORTE DE CIERRE DE CAJA", title_style))
        elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_center))
        elements.append(Spacer(1, 20))

        # --- Información General (Tabla Superior) ---
        data_info = [
            ["ID Sesión:", str(datos_cierre.get('sesion_id', 'N/A')), "Caja:", datos_cierre.get('caja', 'N/A')],
            ["Cajero:", datos_cierre.get('usuario', 'N/A'), "Fecha Cierre:", datos_cierre.get('fecha_cierre', 'N/A')]
        ]

        t_info = Table(data_info, colWidths=[80, 180, 80, 180])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey), # Columna etiquetas 1
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey), # Columna etiquetas 2
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 20))

        # --- Resumen Financiero (Tabla Central) ---
        def fmt_money(val):
            return f"$ {val:,.2f}"

        data_finanzas = [
            ["CONCEPTO", "MONTO"],
            ["Fondo Fijo (Saldo Inicial)", fmt_money(datos_cierre.get('saldo_inicial', 0))],
            ["(+) Total Ingresos", fmt_money(datos_cierre.get('total_ingresos', 0))],
            ["(-) Total Egresos", fmt_money(datos_cierre.get('total_egresos', 0))],
            ["(=) Saldo Teórico (Sistema)", fmt_money(datos_cierre.get('saldo_calculado', 0))],
            ["Saldo Real (Conteo Físico)", fmt_money(datos_cierre.get('saldo_real', 0))],
            ["DIFERENCIA", fmt_money(datos_cierre.get('diferencia', 0))]
        ]

        t_finanzas = Table(data_finanzas, colWidths=[300, 150])
        
        # Estilo condicional para la diferencia (Rojo si negativo, Verde si positivo/cero)
        color_diferencia = colors.red if datos_cierre.get('diferencia', 0) < 0 else colors.green

        t_finanzas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), # Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'), # Alinear números a la derecha
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Negrita fila final
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), # Fondo fila final
            ('TEXTCOLOR', (1, -1), (1, -1), color_diferencia), # Color diferencia
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_finanzas)
        elements.append(Spacer(1, 10))

        # --- Observaciones ---
        obs = datos_cierre.get('observaciones', '')
        if obs:
            elements.append(Paragraph(f"<b>Observaciones:</b> {obs}", styles['Normal']))
            elements.append(Spacer(1, 30))
        else:
            elements.append(Spacer(1, 40))

        # --- Firmas ---
        data_firmas = [
            ["__________________________", "__________________________"],
            ["Firma Cajero", "Firma Supervisor"]
        ]
        t_firmas = Table(data_firmas, colWidths=[250, 250])
        t_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t_firmas)

        # Generar PDF
        doc.build(elements)
        return filepath