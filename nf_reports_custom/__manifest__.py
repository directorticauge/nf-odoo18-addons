# -*- coding: utf-8 -*-
{
    'name': 'NF Reportes Personalizados',
    'version': '18.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Generador de reportes SQL con parámetros de entrada dinámicos',
    'description': '''
        Permite crear reportes SQL personalizados con parámetros de entrada
        (fechas, textos, números) sin necesidad de modificar el código SQL.
        Los resultados se muestran en pantalla y se pueden exportar a CSV.
    ''',
    'author': 'Nestor Forero Salas',
    'website': 'https://www.augesoluciones.com',
    'license': 'OPL-1',
    'images': ['static/description/banner.png'],
    'price': 39.99,
    'currency': 'USD',
    'depends': ['base', 'mail'],
    'data': [
        'security/nf_report_groups.xml',
        'security/ir.model.access.csv',
        'data/nf_report_cron.xml',
        'report/nf_report_pdf.xml',
        'views/nf_report_views.xml',
        'views/nf_report_wizard_views.xml',
        'views/nf_report_log_views.xml',
        'views/nf_schema_browser_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'web_icon': 'nf_reports_custom,static/description/icon.svg',
}
