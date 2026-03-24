# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para asignar automáticamente medios de pago y fechas
        de vencimiento en facturas y notas de crédito POS.
        """
        moves = super(AccountMove, self).create(vals_list)
        
        for move in moves:
            # Solo procesar si es factura o nota de crédito de POS
            if move.pos_order_ids and move.move_type in ('out_invoice', 'out_refund'):
                self._set_payment_defaults(move)
        
        return moves
    
    def write(self, vals):
        """
        Override write para actualizar medios de pago cuando cambia el saldo.
        """
        result = super(AccountMove, self).write(vals)
        
        # Si cambió el saldo residual o la fecha, recalcular
        if 'amount_residual' in vals or 'invoice_date' in vals:
            for move in self:
                if move.pos_order_ids and move.move_type in ('out_invoice', 'out_refund'):
                    self._set_payment_defaults(move)
        
        return result
    
    def _set_payment_defaults(self, move):
        """
        Asigna automáticamente payment_mean_id, forma_de_pago y fecha de vencimiento
        según las reglas de negocio.
        """
        # Obtener los valores de forma_de_pago disponibles
        forma_pago_field = move._fields.get('forma_de_pago')
        if not forma_pago_field:
            return
        
        # Los valores de selección: [(codigo, nombre), ...]
        forma_pago_values = forma_pago_field.selection
        if callable(forma_pago_values):
            forma_pago_values = forma_pago_values(self.env['account.move'])
        
        if not forma_pago_values or len(forma_pago_values) < 2:
            return
        
        # valores[0][0] = primer valor (Contado/Efectivo)
        # valores[1][0] = segundo valor (Crédito)
        valor_contado = forma_pago_values[0][0] if len(forma_pago_values) > 0 else False
        valor_credito = forma_pago_values[1][0] if len(forma_pago_values) > 1 else False
        
        vals_to_update = {}
        
        # REGLA PARA FACTURAS (out_invoice)
        if move.move_type == 'out_invoice':
            # Calcular fecha de vencimiento: +30 días
            if move.invoice_date:
                nueva_fecha = move.invoice_date + timedelta(days=30)
                if move.invoice_date_due != nueva_fecha:
                    vals_to_update['invoice_date_due'] = nueva_fecha
            
            # Asignar medio de pago según saldo residual
            if move.amount_residual > 0.01:
                # Tiene saldo pendiente = Crédito
                if move.payment_mean_id.id != 2:
                    vals_to_update['payment_mean_id'] = 2
                if move.forma_de_pago != valor_credito:
                    vals_to_update['forma_de_pago'] = valor_credito
            else:
                # No tiene saldo pendiente = Efectivo/Contado
                if move.payment_mean_id.id != 10:
                    vals_to_update['payment_mean_id'] = 10
                if move.forma_de_pago != valor_contado:
                    vals_to_update['forma_de_pago'] = valor_contado
        
        # REGLA PARA NOTAS DE CRÉDITO (out_refund)
        elif move.move_type == 'out_refund':
            # Si NO tiene medio de pago DIAN, asignar Efectivo
            if not move.payment_mean_id:
                vals_to_update['payment_mean_id'] = 10
            
            # Asignar forma de pago según saldo residual
            if move.amount_residual > 0.01:
                # Tiene saldo pendiente = Crédito
                if move.payment_mean_id.id != 2:
                    vals_to_update['payment_mean_id'] = 2
                if move.forma_de_pago != valor_credito:
                    vals_to_update['forma_de_pago'] = valor_credito
            else:
                # No tiene saldo pendiente = Efectivo/Contado
                if move.payment_mean_id.id != 10:
                    vals_to_update['payment_mean_id'] = 10
                if move.forma_de_pago != valor_contado:
                    vals_to_update['forma_de_pago'] = valor_contado
        
        # Actualizar si hay cambios
        if vals_to_update:
            # Usar SQL directo para evitar recursión infinita
            for field, value in vals_to_update.items():
                if field == 'invoice_date_due':
                    self.env.cr.execute(
                        "UPDATE account_move SET invoice_date_due = %s WHERE id = %s",
                        (value, move.id)
                    )
                elif field == 'payment_mean_id':
                    self.env.cr.execute(
                        "UPDATE account_move SET payment_mean_id = %s WHERE id = %s",
                        (value, move.id)
                    )
                elif field == 'forma_de_pago':
                    self.env.cr.execute(
                        "UPDATE account_move SET forma_de_pago = %s WHERE id = %s",
                        (value, move.id)
                    )
            
            # Invalidar cache para que Odoo vea los cambios
            move.invalidate_recordset(['invoice_date_due', 'payment_mean_id', 'forma_de_pago'])
