# -*- coding: utf-8 -*-
from odoo import models, fields


class NfIntelligenceDashboard(models.Model):
    _name = 'nf.intelligence.dashboard'
    _description = 'Dashboard de Inteligencia NF'
    _order = 'sequence, name'

    name = fields.Char('Nombre del Dashboard', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    description = fields.Text('Descripción')
    active = fields.Boolean(default=True)
    widget_ids = fields.One2many(
        'nf.intelligence.widget', 'dashboard_id', 'Widgets'
    )
    widget_count = fields.Integer(
        'Widgets', compute='_compute_widget_count', store=False
    )

    def _compute_widget_count(self):
        for rec in self:
            rec.widget_count = len(rec.widget_ids)

    def action_view_dashboard(self):
        self.ensure_one()
        viewer = self.env['nf.intelligence.viewer'].create({
            'dashboard_id': self.id,
        })
        viewer.action_render()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'nf.intelligence.viewer',
            'view_mode': 'form',
            'res_id': viewer.id,
            'target': 'current',
        }
