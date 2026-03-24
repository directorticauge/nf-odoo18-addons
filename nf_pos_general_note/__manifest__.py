# -*- coding: utf-8 -*-
{
    'name': "NF POS General Note (No Invoice Line)",
    'summary': """Permite agregar notas generales en el POS sin generar líneas en la factura contable - Compatible con DIAN""",
    'description': """
    Este módulo permite agregar notas generales a las órdenes del Punto de Venta (POS) 
    sin que estas notas generen líneas adicionales en la factura contable.
    
    Características:
    - Campo de nota general en las órdenes POS
    - Botón en la interfaz POS para agregar/editar notas
    - Las notas aparecen en el recibo impreso
    - Las notas NO generan líneas en account.move (factura contable)
    - Compatible con facturación electrónica DIAN (Colombia)
    
    Esto evita problemas de validación con DIAN al no crear líneas de producto 
    adicionales que no corresponden a productos reales vendidos.
    """,
    'author': 'NF Soluciones',
    'website': 'https://www.augesoluciones.com',
    'category': 'Point of Sale',
    'version': '18.0.1.0',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_views.xml',
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "nf_pos_general_note/static/src/app/store/*.js",
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
