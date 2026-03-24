# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api

EQUIPMENT_STATES = [
    ('available', 'Disponible en Patio'),
    ('assigned', 'Asignado a Cliente'),
    ('maintenance', 'En Mantenimiento'),
    ('lost', 'Por Localizar'),
    ('retired', 'Dado de Baja'),
]


class NfCmdEquipment(models.Model):
    _name = 'nf.cmd.equipment'
    _description = 'Equipo de Comodato'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'equipment_type_id, sequence_number'
    _rec_name = 'name'

    name = fields.Char('Código', compute='_compute_name', store=True)
    sequence_number = fields.Integer('N° Equipo', required=True, tracking=True)
    equipment_type_id = fields.Many2one(
        'nf.cmd.equipment.type', 'Tipo de Equipo',
        required=True, tracking=True, ondelete='restrict',
    )

    # Características del equipo
    brand = fields.Char('Marca')
    model_ref = fields.Char('Modelo / N.C.')
    serial_number = fields.Char('N° Serial')
    capacity = fields.Char('Capacidad', help='Ej: 120x3kg, 2*15KG')
    liters = fields.Char('Litros')
    purchase_date = fields.Date('Fecha de Compra')
    notes = fields.Text('Observaciones')
    active = fields.Boolean(default=True)

    # Estado
    state = fields.Selection(
        EQUIPMENT_STATES, 'Estado', default='available',
        required=True, tracking=True,
    )

    # Asignación activa (desnormalizada para rendimiento en listas)
    assignment_ids = fields.One2many(
        'nf.cmd.assignment', 'equipment_id', 'Historial de Asignaciones',
    )
    assignment_count = fields.Integer(
        '# Asignaciones', compute='_compute_counts', store=False,
    )
    active_assignment_id = fields.Many2one(
        'nf.cmd.assignment', 'Asignación Activa',
        compute='_compute_active_assignment', store=True,
    )
    current_partner_id = fields.Many2one(
        'res.partner', 'Cliente Actual',
        compute='_compute_active_assignment', store=True,
    )
    current_commercial_name = fields.Char(
        'Nombre Comercial',
        compute='_compute_active_assignment', store=True,
    )
    current_route = fields.Char(
        'Ruta', compute='_compute_active_assignment', store=True,
    )
    current_city = fields.Char(
        'Ciudad', compute='_compute_active_assignment', store=True,
    )
    delivery_date = fields.Date(
        'Fecha de Entrega', compute='_compute_active_assignment', store=True,
    )
    days_assigned = fields.Integer(
        'Días Asignado', compute='_compute_days_assigned',
    )

    # Servicios
    service_ids = fields.One2many(
        'nf.cmd.service', 'equipment_id', 'Servicios',
    )
    service_count = fields.Integer(
        '# Servicios', compute='_compute_counts', store=False,
    )

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends('sequence_number', 'equipment_type_id')
    def _compute_name(self):
        for rec in self:
            tipo = rec.equipment_type_id.name if rec.equipment_type_id else 'Equipo'
            rec.name = f'{tipo} #{rec.sequence_number}'

    @api.depends(
        'assignment_ids', 'assignment_ids.state',
        'assignment_ids.partner_id', 'assignment_ids.commercial_name',
        'assignment_ids.route', 'assignment_ids.city',
        'assignment_ids.delivery_date',
    )
    def _compute_active_assignment(self):
        for rec in self:
            active = rec.assignment_ids.filtered(lambda a: a.state == 'active')
            if active:
                assign = active[0]
                rec.active_assignment_id = assign
                rec.current_partner_id = assign.partner_id
                rec.current_commercial_name = assign.commercial_name
                rec.current_route = assign.route
                rec.current_city = assign.city
                rec.delivery_date = assign.delivery_date
            else:
                rec.active_assignment_id = False
                rec.current_partner_id = False
                rec.current_commercial_name = False
                rec.current_route = False
                rec.current_city = False
                rec.delivery_date = False

    @api.depends('delivery_date', 'state')
    def _compute_days_assigned(self):
        today = date.today()
        for rec in self:
            if rec.delivery_date and rec.state == 'assigned':
                rec.days_assigned = (today - rec.delivery_date).days
            else:
                rec.days_assigned = 0

    def _compute_counts(self):
        for rec in self:
            rec.assignment_count = len(rec.assignment_ids)
            rec.service_count = len(rec.service_ids)

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_assign(self):
        self.ensure_one()
        active = self.assignment_ids.filtered(lambda a: a.state == 'active')
        if active:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Equipo ya asignado',
                    'message': f'El equipo ya tiene una asignación activa con {active[0].partner_id.name}.',
                    'type': 'warning',
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': f'Asignar {self.name}',
            'res_model': 'nf.cmd.assignment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_equipment_id': self.id,
                'default_state': 'active',
            },
        }

    def action_return_equipment(self):
        self.ensure_one()
        active = self.assignment_ids.filtered(lambda a: a.state == 'active')
        if active:
            active.write({'state': 'returned', 'return_date': fields.Date.today()})
        self.write({'state': 'available'})

    def action_set_maintenance(self):
        self.ensure_one()
        self.write({'state': 'maintenance'})

    def action_view_assignments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Asignaciones — {self.name}',
            'res_model': 'nf.cmd.assignment',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }

    def action_view_services(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Servicios — {self.name}',
            'res_model': 'nf.cmd.service',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
