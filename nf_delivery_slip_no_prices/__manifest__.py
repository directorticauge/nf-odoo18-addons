{
    "name": "NF Delivery Slip Tirilla (Sin Precios)",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "summary": "Imprime la entrega en formato tirilla sin precios",
    "author": "NF Soluciones",
    "website": "https://www.augesoluciones.com",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "report/report_delivery_slip_receipt.xml",
        "views/print_wizard_views.xml",
        # "views/remove_barcode_report_picking.xml"  # No necesario - botón principal usa tirilla
    ],
    "installable": True,
    "application": False
}
