# -*- coding: utf-8 -*-
{
    'name': 'NF Reports Intelligence',
    'version': '18.0.1.0.0',
    'summary': 'Dashboards, gráficas y tablas dinámicas basadas en NF Reports Custom',
    'description': '''
        Módulo complementario de nf_reports_custom que permite crear dashboards
        con múltiples widgets: tablas, gráficas de barras/líneas/torta,
        tablas dinámicas (pivot) e indicadores KPI, todos basados en los
        reportes SQL definidos en nf_reports_custom.
    ''',
    'author': 'NF',
    'website': 'https://www.augesoluciones.com',
    'category': 'Reporting',
    'depends': ['nf_reports_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/nf_intelligence_dashboard_views.xml',
        'views/nf_intelligence_viewer_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
