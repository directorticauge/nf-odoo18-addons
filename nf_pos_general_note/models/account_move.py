# -*- coding: utf-8 -*-
from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para eliminar líneas de notas al crear facturas desde POS.
        """
        moves = super(AccountMove, self).create(vals_list)
        
        # Procesar cada factura creada
        for move in moves:
            # Solo procesar facturas de POS de tipo 'out_invoice' (ventas)
            if move.move_type == 'out_invoice' and move.pos_order_ids:
                try:
                    self._clean_note_lines(move)
                except Exception:
                    # Si falla, no interrumpir el proceso de creación
                    pass
        
        return moves
    
    def write(self, vals):
        """
        Override write para eliminar líneas de notas al modificar facturas.
        NO ejecutamos limpieza aquí para evitar conflictos con acciones automatizadas.
        La limpieza se hace solo en create() que es cuando se genera la factura desde POS.
        """
        return super(AccountMove, self).write(vals)
    
    def _clean_note_lines(self, move):
        """
        Eliminar líneas que son notas (display_type == 'line_note')
        y agregar su contenido a narration.
        """
        if not move or not move.invoice_line_ids:
            return
        
        # Buscar líneas que son notas: sin producto y display_type == 'line_note'
        note_lines = move.invoice_line_ids.filtered(
            lambda l: not l.product_id and l.display_type == 'line_note'
        )
        
        if note_lines:
            # Extraer texto de las notas
            notes_text = []
            for line in note_lines:
                if line.name and line.name.strip():
                    notes_text.append(line.name.strip())
            
            # Agregar a narration si hay texto
            if notes_text:
                current_narration = move.narration or ''
                notes_combined = '\n'.join(notes_text)
                
                # Solo agregar si no está ya en narration
                if notes_combined not in current_narration:
                    # Usar SQL directo para evitar disparar write() de nuevo
                    if current_narration:
                        new_narration = f"{current_narration}\n\nNotas:\n{notes_combined}"
                    else:
                        new_narration = f"Notas:\n{notes_combined}"
                    
                    # Actualizar directamente en la base de datos
                    self.env.cr.execute(
                        "UPDATE account_move SET narration = %s WHERE id = %s",
                        (new_narration, move.id)
                    )
                    # Invalidar cache para que Odoo vea el cambio
                    move.invalidate_recordset(['narration'])
            
            # Eliminar las líneas de notas
            note_lines.unlink()
            
            # Recalcular totales si existe el método
            if hasattr(move, '_recompute_dynamic_lines'):
                move._recompute_dynamic_lines()
