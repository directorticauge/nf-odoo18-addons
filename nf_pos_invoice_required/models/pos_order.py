# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Forzar to_invoice = True en todas las órdenes si está configurado."""
        for vals in vals_list:
            # Obtener la configuración del POS
            config_id = vals.get('config_id')
            if config_id:
                config = self.env['pos.config'].browse(config_id)
                if config.force_invoice_required:
                    vals['to_invoice'] = True
        
        return super(PosOrder, self).create(vals_list)
    
    def write(self, vals):
        """Evitar que se desmarca to_invoice si está forzado."""
        for order in self:
            if order.config_id.force_invoice_required:
                # Si intentan desmarcar to_invoice, lo forzamos a True
                if 'to_invoice' in vals and not vals['to_invoice']:
                    vals['to_invoice'] = True
        
        return super(PosOrder, self).write(vals)
