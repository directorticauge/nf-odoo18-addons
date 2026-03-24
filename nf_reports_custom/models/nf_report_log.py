# -*- coding: utf-8 -*-
from odoo import models, fields


class NfReportLog(models.Model):
    _name = 'nf.report.log'
    _description = 'Historial de Ejecuciones de Reportes NF'
    _order = 'execution_date desc'

    report_id = fields.Many2one('nf.report', 'Reporte', ondelete='cascade', index=True)
    user_id = fields.Many2one(
        'res.users', 'Usuario',
        default=lambda self: self.env.user,
        readonly=True
    )
    execution_date = fields.Datetime(
        'Fecha de ejecución',
        default=fields.Datetime.now,
        readonly=True
    )
    row_count = fields.Integer('Filas obtenidas', readonly=True)
    execution_time = fields.Float('Tiempo (s)', digits=(6, 3), readonly=True)
    params_summary = fields.Char('Parámetros usados', readonly=True)
    error = fields.Text('Error', readonly=True)
    success = fields.Boolean('Exitoso', default=True, readonly=True)
    export_type = fields.Selection([
        ('screen', 'Pantalla'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
        ('email', 'Correo automático'),
    ], string='Tipo de ejecución', default='screen', readonly=True)
