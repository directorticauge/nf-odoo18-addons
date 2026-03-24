# -*- coding: utf-8 -*-
{
    'name': 'NF Gestión de Comodatos',
    'version': '18.0.1.0.0',
    'category': 'Services',
    'summary': 'Control de inventario y asignación de equipos en comodato (neveras, dispensadores, cuartos fríos)',
    'description': '''
        Gestión completa de equipos en comodato:
        - Inventario de neveras, dispensadores, cuartos fríos y termoneveras
        - Asignación de equipos a clientes con fecha, ruta y ciudad
        - Control de equipos disponibles en patio/bodega interna
        - Historial completo de asignaciones por equipo
        - Registro de salidas y servicios técnicos (mantenimiento, entrega, recogida)
    ''',
    'author': 'Nestor Forero Salas',
    'website': 'https://www.augesoluciones.com',
    'license': 'OPL-1',
    'images': ['static/description/banner.png'],
    'price': 34.99,
    'currency': 'USD',
    'depends': ['base', 'mail'],
    'data': [
        'security/nf_cmd_groups.xml',
        'security/ir.model.access.csv',
        'data/cmd_equipment_type_data.xml',
        'report/cmd_reports.xml',
        'views/cmd_equipment_type_views.xml',
        'views/cmd_equipment_views.xml',
        'views/cmd_assignment_views.xml',
        'views/cmd_service_views.xml',
        'views/cmd_report_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
