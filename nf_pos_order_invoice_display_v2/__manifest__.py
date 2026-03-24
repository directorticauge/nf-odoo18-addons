# -*- coding: utf-8 -*-
{
    'name': "NF Número de Factura, CUFE y QR en Recibo POS (v2)",
    'summary': """Muestra el número de factura, el CUFE y el código QR de la factura electrónica en el recibo del POS, así como en las vistas de Órdenes, Órdenes Pagadas y Análisis de Órdenes.""",
    'description': """
    Este módulo extiende la funcionalidad del Punto de Venta (POS) para mostrar en el recibo
    la información completa de la factura electrónica asociada a cada orden.
    Se agrega a:
        - El recibo impreso del POS: número de factura, CUFE y código QR de la factura electrónica.
        - La vista de lista de órdenes del POS con filtro de búsqueda por número de factura.
        - La vista de órdenes pagadas dentro del POS con filtro de búsqueda por número de factura.
        - El reporte de análisis de órdenes del POS.
    Esto permite una mejor trazabilidad entre las órdenes del POS y sus respectivas facturas electrónicas,
    cumpliendo con los requisitos de la DIAN y facilitando la gestión contable y el control administrativo.
    """,
    'author': "Nestor Forero Salas",
    'website': 'https://www.augesoluciones.com',
    'category': 'point_of_sale',
    'version': '18.0.0.1',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_views.xml',
        'views/pos_order_report_views.xml',
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "nf_pos_order_invoice_display_v2/static/src/app/screens/receipt_screen/receipt/receipt_header/*.xml",
            "nf_pos_order_invoice_display_v2/static/src/app/screens/ticket_screen/*.js",
            "nf_pos_order_invoice_display_v2/static/src/app/screens/ticket_screen/*.xml",
            "nf_pos_order_invoice_display_v2/static/src/app/store/*.js",
        ],
    },
    'images': ['static/description/banner.png'],
    'web_icon': 'nf_pos_order_invoice_display_v2,static/description/icon.svg',
    'application':True,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 58.99
}
