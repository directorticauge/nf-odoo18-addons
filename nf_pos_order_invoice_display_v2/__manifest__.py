# -*- coding: utf-8 -*-
{
    'name': "NF Invoice number in POS Receipt (v2)",
    'summary': """Displays the invoice number on the Point of Sale (POS) receipt, as well as in the Orders, Paid Orders, and Order Analytics views within the POS.""",
    'description': """
    This module extends the Point of Sale (POS) functionality to display the invoice number associated with each order.
    The invoice number is added to:
        - The printed POS receipt.
        - The POS order list view.
        - The paid orders view within the POS.
        - The POS order analysis report.
    This allows for better traceability between POS orders and their respective invoices, facilitating accounting management and administrative control.
    """,
    'author': "NF Soluciones",
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
    'application':True,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 18.99
}
