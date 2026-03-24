{
    "name": "NF POS Network Printer",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Permite configurar impresoras de preparación de red en POS",
    "author": "NF Soluciones",
    "website": "https://www.augesoluciones.com",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "models/pos_printer_views.xml"
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "nf_pos_network_printer/static/src/app/network_printer.js"
        ]
    },
    "installable": True,
    "application": False
}
