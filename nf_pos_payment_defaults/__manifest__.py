# -*- coding: utf-8 -*-
{
    'name': 'NF POS Payment Defaults',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Asignación automática de medios de pago y fechas de vencimiento para facturas y notas de crédito POS',
    'description': """
        Asignación Automática de Pagos POS
        ===================================
        
        Este módulo asigna automáticamente:
        - Medios de pago (payment_mean_id y forma_de_pago)
        - Fechas de vencimiento
        
        Para facturas y notas de crédito generadas desde POS.
        
        Reglas:
        -------
        Facturas (out_invoice):
        - Fecha vencimiento: +30 días desde la fecha de factura
        - Si tiene saldo pendiente > 0.01: Crédito (payment_mean_id=2)
        - Si no tiene saldo pendiente: Efectivo (payment_mean_id=10)
        
        Notas de Crédito (out_refund):
        - Si no tiene medio de pago DIAN: Efectivo (payment_mean_id=10)
        - Si tiene saldo pendiente > 0.01: Crédito (payment_mean_id=2)
        - Si no tiene saldo pendiente: Efectivo (payment_mean_id=10)
        
        Reemplaza las acciones automatizadas del servidor para mejor rendimiento.
    """,
    'author': 'Nestor Forero Salas',
    'website': 'https://www.augesoluciones.com',
    'license': 'OPL-1',
    'images': ['static/description/banner.png'],
    'price': 12.99,
    'currency': 'USD',
    'depends': [
        'point_of_sale',
        'account',
    ],
    'data': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
