# -*- coding: utf-8 -*-
from datetime import date, timedelta
from collections import defaultdict
from odoo import models, fields, api


STATE_LABELS = {
    'available':   'Disponible en Patio',
    'assigned':    'Asignado a Cliente',
    'maintenance': 'En Mantenimiento',
    'lost':        'Por Localizar',
    'retired':     'Dado de Baja',
}
SERVICE_LABELS = {
    'maintenance': 'Mantenimiento',
    'delivery':    'Entrega',
    'pickup':      'Recogida',
    'repair':      'Reparación',
    'inspection':  'Revisión',
    'other':       'Otro',
}
AGRUPADO_LABELS = {
    'ruta':   'Ruta',
    'ciudad': 'Ciudad',
    'tipo':   'Tipo de Equipo',
}


def _fmt_money(value):
    return '{:,.0f}'.format(value or 0)


def _equip_dict(e):
    return {
        'sequence_number': e.sequence_number,
        'tipo':            e.equipment_type_id.name or '-',
        'model_ref':       e.model_ref or '-',
        'brand':           e.brand or '-',
        'capacity':        e.capacity or '-',
        'liters':          e.liters or '-',
        'state':           e.state,
        'state_label':     STATE_LABELS.get(e.state, e.state),
        'commercial_name': e.current_commercial_name or '-',
        'nit_cc':          (e.active_assignment_id.nit_cc if e.active_assignment_id else '') or '-',
        'route':           e.current_route or '-',
        'city':            e.current_city or '-',
        'delivery_date':   str(e.delivery_date) if e.delivery_date else '-',
        'days_assigned':   e.days_assigned,
        'notes':           e.notes or '-',
    }


class NfCmdReportWizard(models.TransientModel):
    _name = 'nf.cmd.report.wizard'
    _description = 'Asistente de Reportes de Comodatos'

    # ── Filtros generales ─────────────────────────────────────────────────────
    report_type = fields.Selection([
        ('inventario',  '1. Relación de Equipos (Inventario)'),
        ('activos',     '2. Comodatos Activos por Ruta/Ciudad'),
        ('servicios',   '5. Informe de Servicios'),
        ('alertas',     '6/7/8. Alertas (perdidos, antiguos, disponibles)'),
        ('resumen',     '9. Resumen Ejecutivo'),
    ], string='Tipo de Reporte', required=True, default='inventario')

    # Filtros equipos
    equipment_type_ids = fields.Many2many(
        'nf.cmd.equipment.type', string='Tipos de Equipo',
        help='Dejar vacío para incluir todos',
    )
    filter_state = fields.Selection(
        [('', 'Todos')] + list(STATE_LABELS.items()),
        string='Estado del Equipo', default='',
    )

    # Filtros servicios
    date_from = fields.Date('Desde', default=lambda self: date.today().replace(day=1))
    date_to   = fields.Date('Hasta', default=fields.Date.today)
    filter_worker = fields.Char('Técnico (filtro)')
    filter_service_type = fields.Selection(
        [('', 'Todos')] + list(SERVICE_LABELS.items()),
        string='Tipo de Servicio', default='',
    )

    # Opciones agrupación (reporte activos)
    group_by = fields.Selection([
        ('ruta',   'Ruta'),
        ('ciudad', 'Ciudad'),
        ('tipo',   'Tipo de Equipo'),
    ], string='Agrupar por', default='ruta')

    # Alerta umbral meses
    umbral_meses = fields.Integer('Meses sin devolución (umbral alerta)', default=6)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def action_print(self):
        self.ensure_one()
        report_map = {
            'inventario': 'nf_support_cmd.action_report_cmd_inventario',
            'activos':    'nf_support_cmd.action_report_cmd_activos',
            'servicios':  'nf_support_cmd.action_report_cmd_servicios',
            'alertas':    'nf_support_cmd.action_report_cmd_alertas',
            'resumen':    'nf_support_cmd.action_report_cmd_resumen',
        }
        return self.env.ref(report_map[self.report_type]).report_action(self)

    # ── Datos para QWeb ───────────────────────────────────────────────────────

    def _get_equipos_domain(self):
        domain = [('active', 'in', [True, False])]
        if self.equipment_type_ids:
            domain.append(('equipment_type_id', 'in', self.equipment_type_ids.ids))
        if self.filter_state:
            domain.append(('state', '=', self.filter_state))
        return domain

    def get_data_inventario(self):
        self.ensure_one()
        equipos = self.env['nf.cmd.equipment'].search(
            self._get_equipos_domain(),
            order='equipment_type_id, sequence_number',
        )
        return {
            'fecha_generacion': str(date.today()),
            'total_equipos':    len(equipos),
            'filtro_tipo':      ', '.join(self.equipment_type_ids.mapped('name')) or None,
            'filtro_estado':    STATE_LABELS.get(self.filter_state) if self.filter_state else None,
            'equipos':          [_equip_dict(e) for e in equipos],
        }

    def get_data_activos(self):
        self.ensure_one()
        domain = [('state', '=', 'assigned')]
        if self.equipment_type_ids:
            domain.append(('equipment_type_id', 'in', self.equipment_type_ids.ids))
        equipos = self.env['nf.cmd.equipment'].search(
            domain, order='current_route, equipment_type_id, sequence_number',
        )

        grupos_dict = defaultdict(list)
        for e in equipos:
            if self.group_by == 'ruta':
                key = e.current_route or 'Sin Ruta'
            elif self.group_by == 'ciudad':
                key = e.current_city or 'Sin Ciudad'
            else:
                key = e.equipment_type_id.name or 'Sin Tipo'
            grupos_dict[key].append(_equip_dict(e))

        grupos = [
            {'label': k, 'count': len(v), 'equipos': v}
            for k, v in sorted(grupos_dict.items())
        ]
        return {
            'fecha_generacion': str(date.today()),
            'total_activos':    len(equipos),
            'agrupado_por':     AGRUPADO_LABELS.get(self.group_by, self.group_by),
            'grupos':           grupos,
        }

    def get_data_servicios(self):
        self.ensure_one()
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.filter_worker:
            domain.append(('worker', 'ilike', self.filter_worker))
        if self.filter_service_type:
            domain.append(('service_type', '=', self.filter_service_type))
        if self.equipment_type_ids:
            domain.append(('equipment_type_id', 'in', self.equipment_type_ids.ids))

        servicios = self.env['nf.cmd.service'].search(domain, order='date desc')
        total_valor = sum(servicios.mapped('value'))

        rows = []
        for s in servicios:
            rows.append({
                'date':              str(s.date),
                'service_type_label': SERVICE_LABELS.get(s.service_type, s.service_type),
                'equipo':            s.equipment_id.name or '-',
                'tipo_equipo':       s.equipment_type_id.name or '-',
                'client_name':       s.client_name or (s.partner_id.name if s.partner_id else '-'),
                'worker':            s.worker or '-',
                'value':             s.value,
                'value_fmt':         _fmt_money(s.value),
                'notes':             s.notes or '-',
            })

        return {
            'fecha_desde':          str(self.date_from),
            'fecha_hasta':          str(self.date_to),
            'total_servicios':      len(servicios),
            'total_valor':          _fmt_money(total_valor),
            'filtro_tecnico':       self.filter_worker or None,
            'filtro_tipo_servicio': SERVICE_LABELS.get(self.filter_service_type) if self.filter_service_type else None,
            'servicios':            rows,
        }

    def get_data_alertas(self):
        self.ensure_one()
        hoy = date.today()
        umbral_dias = self.umbral_meses * 30

        # Perdidos
        perdidos = self.env['nf.cmd.equipment'].search([('state', '=', 'lost')])

        # Asignados hace más de umbral_meses meses
        corte = hoy - timedelta(days=umbral_dias)
        antiguos = self.env['nf.cmd.equipment'].search([
            ('state', '=', 'assigned'),
            ('delivery_date', '!=', False),
            ('delivery_date', '<=', corte),
        ], order='delivery_date asc')

        # En patio (sin asignación nunca o devueltos)
        sin_movimiento = self.env['nf.cmd.equipment'].search([
            ('state', '=', 'available'),
        ], order='equipment_type_id, sequence_number')

        return {
            'fecha_generacion': str(hoy),
            'umbral_meses':     self.umbral_meses,
            'perdidos':         [_equip_dict(e) for e in perdidos],
            'antiguos':         [_equip_dict(e) for e in antiguos],
            'sin_movimiento':   [_equip_dict(e) for e in sin_movimiento],
        }

    def get_data_resumen(self):
        self.ensure_one()
        hoy = date.today()
        todos = self.env['nf.cmd.equipment'].search([])

        # Por estado
        por_estado = []
        for state, label in STATE_LABELS.items():
            count = sum(1 for e in todos if e.state == state)
            if count:
                por_estado.append({'label': label, 'state': state, 'count': count})

        # Por tipo
        tipos = self.env['nf.cmd.equipment.type'].search([])
        por_tipo = []
        for t in tipos:
            equips = todos.filtered(lambda e, tid=t.id: e.equipment_type_id.id == tid)
            if equips:
                por_tipo.append({
                    'tipo':       t.name,
                    'total':      len(equips),
                    'asignados':  sum(1 for e in equips if e.state == 'assigned'),
                    'disponibles': sum(1 for e in equips if e.state == 'available'),
                })

        # Servicios del período
        servicios = self.env['nf.cmd.service'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        svc_por_tipo = defaultdict(lambda: {'count': 0, 'valor': 0.0})
        for s in servicios:
            svc_por_tipo[s.service_type]['count'] += 1
            svc_por_tipo[s.service_type]['valor'] += s.value
        servicios_por_tipo = [
            {
                'tipo':      SERVICE_LABELS.get(k, k),
                'count':     v['count'],
                'valor_fmt': _fmt_money(v['valor']),
            }
            for k, v in sorted(svc_por_tipo.items())
        ]
        total_valor_svc = sum(s.value for s in servicios)

        # Top rutas
        rutas = defaultdict(int)
        for e in todos.filtered(lambda x: x.state == 'assigned' and x.current_route):
            rutas[e.current_route] += 1
        top_rutas = [
            {'ruta': r, 'count': c}
            for r, c in sorted(rutas.items(), key=lambda x: -x[1])[:8]
        ]

        return {
            'fecha_generacion':       str(hoy),
            'fecha_desde':            str(self.date_from),
            'fecha_hasta':            str(self.date_to),
            'total_equipos':          len(todos),
            'por_estado':             por_estado,
            'por_tipo':               por_tipo,
            'servicios_por_tipo':     servicios_por_tipo,
            'total_servicios':        len(servicios),
            'total_valor_servicios':  _fmt_money(total_valor_svc),
            'top_rutas':              top_rutas,
        }


class NfCmdReportAbstract(models.AbstractModel):
    """Proveedor de datos QWeb para los reportes del wizard."""
    _name = 'report.nf_support_cmd.report_cmd_inventario'
    _description = 'Reporte Inventario QWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['nf.cmd.report.wizard'].browse(docids)
        return {'data': wizard.get_data_inventario(), 'doc_ids': docids, 'doc_model': 'nf.cmd.report.wizard'}


class NfCmdReportActivosAbstract(models.AbstractModel):
    _name = 'report.nf_support_cmd.report_cmd_activos'
    _description = 'Reporte Activos QWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['nf.cmd.report.wizard'].browse(docids)
        return {'data': wizard.get_data_activos(), 'doc_ids': docids, 'doc_model': 'nf.cmd.report.wizard'}


class NfCmdReportServiciosAbstract(models.AbstractModel):
    _name = 'report.nf_support_cmd.report_cmd_servicios'
    _description = 'Reporte Servicios QWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['nf.cmd.report.wizard'].browse(docids)
        return {'data': wizard.get_data_servicios(), 'doc_ids': docids, 'doc_model': 'nf.cmd.report.wizard'}


class NfCmdReportAlertasAbstract(models.AbstractModel):
    _name = 'report.nf_support_cmd.report_cmd_alertas'
    _description = 'Reporte Alertas QWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['nf.cmd.report.wizard'].browse(docids)
        return {'data': wizard.get_data_alertas(), 'doc_ids': docids, 'doc_model': 'nf.cmd.report.wizard'}


class NfCmdReportResumenAbstract(models.AbstractModel):
    _name = 'report.nf_support_cmd.report_cmd_resumen'
    _description = 'Reporte Resumen QWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['nf.cmd.report.wizard'].browse(docids)
        return {'data': wizard.get_data_resumen(), 'doc_ids': docids, 'doc_model': 'nf.cmd.report.wizard'}
