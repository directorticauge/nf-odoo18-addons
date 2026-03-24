# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NfCmdService(models.Model):
    _name = 'nf.cmd.service'
    _description = 'Salida de Servicio / Mantenimiento de Comodato'
    _order = 'date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    date = fields.Date('Fecha', required=True, default=fields.Date.today)

    equipment_id = fields.Many2one(
        'nf.cmd.equipment', 'Equipo', required=True, ondelete='restrict',
    )
    equipment_type_id = fields.Many2one(
        related='equipment_id.equipment_type_id', store=True, readonly=True,
    )
    sequence_number = fields.Integer(
        related='equipment_id.sequence_number', store=True, readonly=True,
    )

    partner_id = fields.Many2one('res.partner', 'Cliente')
    client_name = fields.Char('Nombre del Lugar / Cliente')

    service_type = fields.Selection([
        ('maintenance', 'Mantenimiento'),
        ('delivery', 'Entrega'),
        ('pickup', 'Recogida'),
        ('repair', 'Reparación'),
        ('inspection', 'Revisión'),
        ('other', 'Otro'),
    ], 'Tipo de Servicio', default='maintenance', required=True)

    value = fields.Float('Valor del Servicio', digits=(12, 0))
    worker = fields.Char('Técnico / Trabajador')
    notes = fields.Text('Observaciones')

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends('date', 'equipment_id', 'client_name', 'partner_id')
    def _compute_display_name(self):
        for rec in self:
            date_str = str(rec.date) if rec.date else ''
            equip = rec.equipment_id.name or ''
            client = rec.client_name or (rec.partner_id.name if rec.partner_id else '')
            rec.display_name = f'{date_str} | {equip} | {client}'

    # ── Onchange ──────────────────────────────────────────────────────────────

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id and not self.client_name:
            self.client_name = self.partner_id.name

    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id and self.equipment_id.current_partner_id:
            if not self.partner_id:
                self.partner_id = self.equipment_id.current_partner_id
            if not self.client_name:
                self.client_name = self.equipment_id.current_commercial_name
