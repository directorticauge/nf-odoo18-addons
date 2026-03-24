{
    "name": "NF Delivery Slip Tirilla (Sin Precios)",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "summary": "Imprime la entrega en formato tirilla sin precios",
    "author": "Nestor Forero Salas",
    "website": "https://www.augesoluciones.com",
    "license": "OPL-1",
    "images": ["static/description/banner.png"],
    "price": 9.99,
    "currency": "USD",
    "depends": ["stock"],
    "data": [
        "report/report_delivery_slip_receipt.xml",
        "views/print_wizard_views.xml",
        # "views/remove_barcode_report_picking.xml"  # No necesario - botón principal usa tirilla
    ],
    "installable": True,
    "application": True,
}
