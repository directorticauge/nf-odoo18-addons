# -*- coding: utf-8 -*-
{
    'name': 'NF POS - Factura Obligatoria',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Hace que la opción Recibo/Factura en el POS sea obligatoria',
    'description': """
        POS - Factura Obligatoria
        =========================
        
        Este módulo hace que la opción "Recibo/Factura" en el Punto de Venta
        siempre esté marcada y no se pueda desmarcar.
        
        Características:
        ----------------
        * El checkbox "Recibo/Factura" siempre está marcado por defecto
        * No se puede desmarcar (obligatorio)
        * Todas las órdenes del POS generarán factura automáticamente
        * Se fuerza a nivel de backend para garantizar que no se omita
    """,
    'author': 'Nestor Forero Salas',
    'website': 'https://www.augesoluciones.com',
    'license': 'OPL-1',
    'images': ['static/description/banner.png'],
    'price': 7.99,
    'currency': 'USD',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
