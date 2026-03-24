# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NfCmdAssignment(models.Model):
    _name = 'nf.cmd.assignment'
    _description = 'Asignación de Equipo en Comodato'
    _inherit = ['mail.thread']
    _order = 'delivery_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    equipment_id = fields.Many2one(
        'nf.cmd.equipment', 'Equipo',
        required=True, ondelete='cascade', tracking=True,
    )
    equipment_type_id = fields.Many2one(
        related='equipment_id.equipment_type_id', store=True, readonly=True,
    )
    sequence_number = fields.Integer(
        related='equipment_id.sequence_number', store=True, readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner', 'Cliente', tracking=True,
    )
    commercial_name = fields.Char('Nombre Comercial', tracking=True)
    nit_cc = fields.Char('NIT / C.C.')

    delivery_date = fields.Date(
        'Fecha de Entrega', required=True,
        default=fields.Date.today, tracking=True,
    )
    return_date = fields.Date('Fecha de Devolución', tracking=True)

    route = fields.Char('Ruta', tracking=True)
    city = fields.Char('Ciudad', tracking=True)

    state = fields.Selection([
        ('active', 'Activo'),
        ('returned', 'Devuelto'),
        ('cancelled', 'Cancelado'),
    ], 'Estado', default='active', required=True, tracking=True)

    days_assigned = fields.Integer('Días Asignado', compute='_compute_days')
    notes = fields.Text('Observaciones')

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends('equipment_id', 'partner_id', 'commercial_name')
    def _compute_display_name(self):
        for rec in self:
            equip = rec.equipment_id.name or 'Equipo'
            client = rec.commercial_name or (rec.partner_id.name if rec.partner_id else 'Sin cliente')
            rec.display_name = f'{equip} → {client}'

    @api.depends('delivery_date', 'return_date', 'state')
    def _compute_days(self):
        from datetime import date
        today = date.today()
        for rec in self:
            if rec.delivery_date:
                end = rec.return_date or today
                rec.days_assigned = (end - rec.delivery_date).days
            else:
                rec.days_assigned = 0

    # ── Onchange ──────────────────────────────────────────────────────────────

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id and not self.commercial_name:
            self.commercial_name = self.partner_id.name
        if self.partner_id and not self.nit_cc:
            self.nit_cc = self.partner_id.vat or ''

    # ── CRUD ──────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'active':
                rec.equipment_id.write({'state': 'assigned'})
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') == 'returned' or vals.get('state') == 'cancelled':
            for rec in self:
                still_active = rec.equipment_id.assignment_ids.filtered(
                    lambda a: a.state == 'active' and a.id != rec.id
                )
                if not still_active:
                    rec.equipment_id.write({'state': 'available'})
        elif vals.get('state') == 'active':
            for rec in self:
                rec.equipment_id.write({'state': 'assigned'})
        return result

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_return(self):
        self.write({'state': 'returned', 'return_date': fields.Date.today()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
