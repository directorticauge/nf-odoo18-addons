# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    general_note = fields.Text(
        string="Nota General",
        help="Nota general de la orden que NO genera líneas en la factura contable. "
             "Esta nota es solo informativa y aparece en el recibo pero no afecta "
             "la contabilidad ni la facturación electrónica DIAN."
    )
    
    def _prepare_invoice_vals(self):
        """
        Override para agregar la nota general a la factura cuando se crea desde el POS.
        """
        vals = super(PosOrder, self)._prepare_invoice_vals()
        
        # Agregar la nota como narration (comentario interno) en lugar de línea
        if self.general_note:
            current_narration = vals.get('narration', '')
            if current_narration:
                vals['narration'] = f"{current_narration}\n\nNota General: {self.general_note}"
            else:
                vals['narration'] = f"Nota General: {self.general_note}"
            # Agregar solo el valor en order_reference (sin prefijo)
            vals['order_reference'] = self.general_note
        
        return vals

    
    def _prepare_invoice_line(self, order_line):
        """
        Override para evitar crear líneas de invoice con precio 0 o vacías (notas).
        """
        # Si la línea tiene precio 0 o cantidad 0, no crear línea de factura (es una nota)
        if order_line.price_unit == 0 or order_line.qty == 0:
            return False
        
        return super(PosOrder, self)._prepare_invoice_line(order_line)
    
    def action_pos_order_invoice(self):
        """
        Override para:
        1. Agregar general_note a términos y condiciones (si no está ya)
        2. Eliminar líneas con precio 0 o vacías (notas) después de crear la factura
        """
        result = super(PosOrder, self).action_pos_order_invoice()
        
        if self.account_move:
            # 1. Agregar general_note si existe Y no está ya en narration
            if self.general_note:
                current_narration = self.account_move.narration or ''
                # Solo agregar si no está ya (evitar duplicación)
                if f"Nota General: {self.general_note}" not in current_narration:
                    if current_narration:
                        self.account_move.narration = f"{current_narration}\n\nNota General: {self.general_note}"
                    else:
                        self.account_move.narration = f"Nota General: {self.general_note}"
                # Agregar solo el valor en order_reference (sin prefijo)
                self.account_move.order_reference = self.general_note
            
            # 2. Eliminar líneas de notas (sin producto, precio 0, o cantidad 0)
            lines_to_remove = self.account_move.invoice_line_ids.filtered(
                lambda l: (
                    not l.product_id or  # Sin producto asociado = nota contable
                    l.price_unit == 0 or  # Precio cero
                    l.quantity == 0 or    # Cantidad cero
                    (l.price_subtotal == 0 and l.price_total == 0)  # Total cero
                )
            )
            
            if lines_to_remove:
                lines_to_remove.unlink()
                # Recalcular totales
                self.account_move._recompute_dynamic_lines()
        
        return result
    
    @api.model
    def _order_fields(self, ui_order):
        """
        Extender para incluir el campo general_note desde el POS frontend.
        """
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        
        if ui_order.get('general_note'):
            order_fields['general_note'] = ui_order['general_note']
        
        return order_fields
    
    @api.model
    def _loader_params_pos_order(self):
        """
        Cargar el campo general_note en el POS para órdenes existentes.
        """
        result = super()._loader_params_pos_order()
        if 'search_params' in result:
            if 'fields' in result['search_params']:
                result['search_params']['fields'].append('general_note')
        return result
