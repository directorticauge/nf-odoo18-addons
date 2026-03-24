# -*- coding: utf-8 -*-
from odoo import models, fields


class NfCmdEquipmentType(models.Model):
    _name = 'nf.cmd.equipment.type'
    _description = 'Tipo de Equipo de Comodato'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean(default=True)
    equipment_count = fields.Integer(
        '# Equipos', compute='_compute_equipment_count',
    )

    def _compute_equipment_count(self):
        for rec in self:
            rec.equipment_count = self.env['nf.cmd.equipment'].search_count(
                [('equipment_type_id', '=', rec.id)]
            )

    def action_view_equipments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Equipos — {self.name}',
            'res_model': 'nf.cmd.equipment',
            'view_mode': 'list,form',
            'domain': [('equipment_type_id', '=', self.id)],
        }
