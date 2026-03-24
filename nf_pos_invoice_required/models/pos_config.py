# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    force_invoice_required = fields.Boolean(
        string='Factura Obligatoria',
        default=True,
        help='Si está marcado, el checkbox "Recibo/Factura" siempre estará activo y obligatorio en este POS.'
    )
