from odoo import models, fields

class PosPrinterNetwork(models.Model):
    _inherit = "pos.printer"

    network_print_url = fields.Char(
        string="URL de impresora de red",
        help="URL del servicio de impresión (ejemplo: https://192.168.1.77:5001/print)"
    )

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_printer(self):
        """Add network_print_url to fields loaded in POS"""
        result = super()._loader_params_pos_printer()
        result['search_params']['fields'].append('network_print_url')
        return result
