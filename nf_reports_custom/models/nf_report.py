# -*- coding: utf-8 -*-
import re
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class NfReport(models.Model):
    _name = 'nf.report'
    _description = 'Reporte Personalizado NF'
    _order = 'sequence, name'

    name = fields.Char('Nombre del Reporte', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    category = fields.Char('Categoría', default='General')
    description = fields.Text('Descripción')
    is_favorite = fields.Boolean('Favorito', default=False)
    query = fields.Text(
        'Consulta SQL', required=True,
        help=(
            "Consulta SQL SELECT. Use la sintaxis de psycopg2 para los parámetros:\n"
            "  %(nombre_parametro)s\n\n"
            "Ejemplo:\n"
            "SELECT po.name, po.date_order\n"
            "FROM pos_order po\n"
            "WHERE po.date_order::date BETWEEN %(fecha_desde)s AND %(fecha_hasta)s"
        )
    )
    param_ids = fields.One2many('nf.report.param', 'report_id', 'Parámetros de Entrada')
    note = fields.Text('Nota interna')
    active = fields.Boolean(default=True)

    # ── Control de acceso ────────────────────────────────────────
    group_ids = fields.Many2many(
        'res.groups',
        'nf_report_group_rel', 'report_id', 'group_id',
        string='Grupos con acceso',
        help='Grupos que pueden ver y ejecutar este reporte. Si está vacío (y tampoco hay usuarios), todos tienen acceso.'
    )
    user_ids = fields.Many2many(
        'res.users',
        'nf_report_user_rel', 'report_id', 'user_id',
        string='Usuarios con acceso',
        help='Usuarios específicos que pueden ver y ejecutar este reporte. Se combina con los Grupos con acceso (cualquiera de los dos da acceso).'
    )

    # ── Programación automática ──────────────────────────────────
    schedule_active = fields.Boolean('Envío automático', default=False)
    schedule_frequency = fields.Selection([
        ('daily', 'Diario'),
        ('weekly', 'Semanal (lunes)'),
        ('monthly', 'Mensual (día 1)'),
    ], string='Frecuencia', default='daily')
    schedule_email_to = fields.Char('Enviar a (correos)',
                                    help='Correos separados por coma')
    schedule_email_subject = fields.Char('Asunto del correo')

    # ── Estadísticas ─────────────────────────────────────────────
    log_count = fields.Integer('Ejecuciones', compute='_compute_log_count', store=False)

    def _compute_log_count(self):
        for rec in self:
            rec.log_count = self.env['nf.report.log'].search_count(
                [('report_id', '=', rec.id)]
            )

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historial: {self.name}',
            'res_model': 'nf.report.log',
            'view_mode': 'list,form',
            'domain': [('report_id', '=', self.id)],
        }

    # ── Acceso por grupo / usuario ───────────────────────────────
    def _user_has_access(self):
        # Si no hay restricciones, acceso libre
        if not self.group_ids and not self.user_ids:
            return True
        # Acceso si el usuario está en la lista de usuarios o en algún grupo
        if self.user_ids and self.env.user in self.user_ids:
            return True
        if self.group_ids and bool(self.group_ids & self.env.user.groups_id):
            return True
        return False

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, **kwargs):
        results = super().search(domain, offset=offset, limit=limit, order=order, **kwargs)
        if self.env.user.has_group('nf_reports_custom.group_nf_report_manager'):
            return results
        return results.filtered(lambda r: r._user_has_access())

    @api.constrains('query')
    def _check_query_security(self):
        for record in self:
            record._validate_query(record.query)

    def _validate_query(self, query):
        if not query:
            return
        clean = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        clean = re.sub(r'--[^\n]*', '', clean)
        clean = clean.strip().upper()

        if not (clean.startswith('SELECT') or clean.startswith('WITH')):
            raise ValidationError(
                'Solo se permiten consultas SELECT o WITH (CTEs de lectura).'
            )

        forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
                     'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
        for keyword in forbidden:
            if re.search(r'\b' + keyword + r'\b', clean):
                raise ValidationError(
                    f'Consulta no permitida: contiene la instrucción {keyword}.'
                )

    def action_run_report(self):
        self.ensure_one()
        # Verificar acceso (admins siempre pueden ejecutar)
        if not self.env.user.has_group('nf_reports_custom.group_nf_report_manager'):
            if not self._user_has_access():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Acceso restringido',
                        'message': 'No tiene permiso para ejecutar este reporte. Contacte al administrador.',
                        'type': 'warning',
                        'sticky': True,
                    },
                }
        param_lines = []
        for param in self.param_ids.sorted('sequence'):
            hint_parts = []
            if param.hint:
                hint_parts.append(param.hint)
            if param.default_value:
                hint_parts.append(f'Defecto: {param.default_value}')
            vals = {
                'param_id': param.id,
                'sequence': param.sequence,
                'name': param.name,
                'param_label': param.param_label,
                'param_hint': ' | '.join(hint_parts),
                'default_expr': param.default_value or '',
                'param_type': param.param_type,
                'required': param.required,
            }
            resolved = param._resolve_default()
            if resolved is not None:
                vals['value_input'] = str(resolved)
            param_lines.append((0, 0, vals))

        wizard = self.env['nf.report.wizard'].create({
            'report_id': self.id,
            'param_line_ids': param_lines,
        })
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'nf.report.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': {'dialog_size': 'xl'},
        }

    # ── Programación automática (cron) ──────────────────────────────
    @api.model
    def action_run_scheduled(self):
        """Invocado por el cron. Ejecuta reportes según su frecuencia."""
        today = date.today()
        records = self.search([
            ('schedule_active', '=', True),
            ('active', '=', True),
        ])
        for report in records:
            freq = report.schedule_frequency
            if freq == 'weekly' and today.weekday() != 0:
                continue
            if freq == 'monthly' and today.day != 1:
                continue
            try:
                report._execute_and_email()
            except Exception as e:
                _logger.error('Error en reporte programado "%s": %s', report.name, e)

    def _execute_and_email(self):
        """Ejecuta el reporte y envía el CSV por correo."""
        import csv
        import io
        import base64
        import time

        emails = [
            e.strip()
            for e in (self.schedule_email_to or '').split(',')
            if e.strip()
        ]
        if not emails:
            _logger.warning('Reporte "%s": no hay correos configurados.', self.name)
            return

        start = time.time()
        try:
            self.env.cr.execute(self.query, {})
            rows = self.env.cr.fetchall()
            cols = [desc[0] for desc in self.env.cr.description]
        except Exception as e:
            self.env['nf.report.log'].create({
                'report_id': self.id,
                'row_count': 0,
                'execution_time': 0,
                'error': str(e),
                'success': False,
                'export_type': 'email',
            })
            raise

        elapsed = round(time.time() - start, 3)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(cols)
        writer.writerows(
            [str(v) if v is not None else '' for v in row] for row in rows
        )
        data = base64.b64encode(output.getvalue().encode('utf-8-sig'))
        filename = f"{self.name.replace(' ', '_')}.csv"

        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': data,
            'mimetype': 'text/csv',
        })

        subject = (
            self.schedule_email_subject
            or f'Reporte: {self.name} — {date.today().strftime("%d/%m/%Y")}'
        )
        body = (
            f'<p>Se adjunta el reporte <b>{self.name}</b> '
            f'generado automáticamente el {date.today().strftime("%d/%m/%Y")}.</p>'
            f'<p>Filas: <b>{len(rows)}</b> | Tiempo: <b>{elapsed}s</b></p>'
        )

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_to': ', '.join(emails),
            'attachment_ids': [(4, attachment.id)],
        }).send()

        self.env['nf.report.log'].create({
            'report_id': self.id,
            'row_count': len(rows),
            'execution_time': elapsed,
            'success': True,
            'export_type': 'email',
        })


class NfReportParam(models.Model):
    _name = 'nf.report.param'
    _description = 'Parámetro de Reporte NF'
    _order = 'sequence, id'

    report_id = fields.Many2one('nf.report', required=True, ondelete='cascade')
    sequence = fields.Integer('Orden', default=10)
    name = fields.Char(
        'Nombre técnico', required=True,
        help="Nombre usado en SQL como %(nombre)s. Solo letras, números y guión bajo."
    )
    param_label = fields.Char('Etiqueta en pantalla', required=True)
    hint = fields.Char(
        'Ayuda / Ejemplo',
        help="Texto de ayuda que se muestra al usuario al ingresar el valor."
    )
    param_type = fields.Selection([
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('char', 'Texto'),
        ('integer', 'Número entero'),
        ('float', 'Número decimal'),
        ('boolean', 'Sí/No'),
    ], string='Tipo', required=True, default='date')
    required = fields.Boolean('Obligatorio', default=True)
    default_value = fields.Char(
        'Valor por defecto',
        help=(
            "Valor fijo o expresión dinámica:\n"
            "  today                → fecha de hoy\n"
            "  first_of_month       → primer día del mes actual\n"
            "  last_of_month        → último día del mes actual\n"
            "  first_of_last_month  → primer día del mes anterior\n"
            "  last_of_last_month   → último día del mes anterior\n"
            "  Para fecha fija use formato: YYYY-MM-DD"
        )
    )

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', record.name):
                raise ValidationError(
                    f'El nombre técnico "{record.name}" solo puede contener '
                    'letras, números y guión bajo, y debe empezar con letra o _'
                )

    def _resolve_default(self):
        """Resuelve default_value, incluyendo expresiones dinámicas de fecha."""
        val = (self.default_value or '').strip()
        if not val:
            return None

        today = date.today()
        dynamic = {
            'today': today,
            'first_of_month': today.replace(day=1),
            'last_of_month': (
                today.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            ),
            'first_of_last_month': today.replace(day=1) - relativedelta(months=1),
            'last_of_last_month': today.replace(day=1) - relativedelta(days=1),
        }
        if val.lower() in dynamic:
            resolved = dynamic[val.lower()]
            if self.param_type == 'datetime':
                return datetime.combine(resolved, datetime.min.time())
            return resolved

        if self.param_type == 'date':
            try:
                return datetime.strptime(val, '%Y-%m-%d').date()
            except ValueError:
                return None
        if self.param_type == 'datetime':
            try:
                return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None

        return val
