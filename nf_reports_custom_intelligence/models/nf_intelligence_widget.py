# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class NfIntelligenceWidget(models.Model):
    _name = 'nf.intelligence.widget'
    _description = 'Widget de Dashboard NF Intelligence'
    _order = 'sequence, id'

    dashboard_id = fields.Many2one(
        'nf.intelligence.dashboard', 'Dashboard',
        ondelete='cascade', required=True
    )
    sequence = fields.Integer('Secuencia', default=10)
    name = fields.Char('Título del widget', required=True)
    report_id = fields.Many2one('nf.report', 'Reporte', required=True)

    widget_type = fields.Selection([
        ('table',  'Tabla'),
        ('bar',    'Gráfica de Barras'),
        ('line',   'Gráfica de Líneas'),
        ('pie',    'Gráfica Circular (Torta)'),
        ('pivot',  'Tabla Dinámica (Pivot)'),
        ('kpi',    'KPI / Indicador'),
        ('matrix', 'Mapa de Calor (Matriz)'),
    ], string='Tipo de widget', required=True, default='table')

    # ── Mapeo de columnas ──────────────────────────────────────
    label_field = fields.Char(
        'Campo Etiqueta (Eje X / Filas)',
        help='Nombre exacto de la columna SQL para etiquetas en gráficas o filas en pivot.\n'
             'Ejemplo: "metodo_pago", "fecha", "vendedor"'
    )
    value_field = fields.Char(
        'Campo Valor (Eje Y / Medida)',
        help='Nombre exacto de la columna numérica para el valor o medida.\n'
             'Ejemplo: "total", "cantidad", "monto"'
    )
    col_field = fields.Char(
        'Campo Columnas (solo Pivot)',
        help='Para tabla dinámica: columna que forma las cabeceras de columna.\n'
             'Ejemplo: "mes", "categoria", "tipo"'
    )
    agg_func = fields.Selection([
        ('sum',   'Suma'),
        ('count', 'Conteo'),
        ('avg',   'Promedio'),
        ('min',   'Mínimo'),
        ('max',   'Máximo'),
    ], string='Función de agregación', default='sum')

    # ── Parámetros del reporte (tabla estructurada) ────────────
    widget_param_ids = fields.One2many(
        'nf.intelligence.widget.param', 'widget_id', 'Parámetros',
    )
    # Legado JSON (fallback cuando widget_param_ids está vacío)
    param_vals = fields.Text('Parámetros JSON (legado)', default='{}')
    report_param_names = fields.Char(
        'Parámetros disponibles',
        compute='_compute_report_param_names',
        store=False,
    )
    detected_columns = fields.Text(
        'Columnas detectadas',
        readonly=True,
        help='Pulse "Detectar columnas" para ver las columnas que retorna el SQL '
             'con los parámetros actuales.',
    )

    # ── Columnas detectadas (selectores) ──────────────────────
    available_column_ids = fields.One2many(
        'nf.intelligence.widget.column', 'widget_id',
        string='Columnas disponibles', readonly=True,
    )
    label_field_id = fields.Many2one(
        'nf.intelligence.widget.column',
        string='Campo Etiqueta (Eje X / Filas)',
        domain="[('widget_id', '=', id)]",
        ondelete='set null',
        help='Columna para etiquetas — eje X en gráficas, filas en pivot/tabla',
    )
    value_field_id = fields.Many2one(
        'nf.intelligence.widget.column',
        string='Campo Valor (Eje Y / Medida)',
        domain="[('widget_id', '=', id), ('col_type', '=', 'numeric')]",
        ondelete='set null',
        help='Columna numérica — eje Y en gráficas, medida en KPI y pivot. '
             'Solo muestra columnas numéricas detectadas.',
    )
    col_field_id = fields.Many2one(
        'nf.intelligence.widget.column',
        string='Campo Columnas (Pivot / Matriz)',
        domain="[('widget_id', '=', id)]",
        ondelete='set null',
        help='Para Pivot y Mapa de Calor: columna que forma las cabeceras horizontales',
    )

    # ── Vista previa ────────────────────────────────────
    preview_html = fields.Html('Vista previa', sanitize=False, readonly=True)

    # ── Visual ────────────────────────────────────────────────
    chart_color = fields.Char('Color principal', default='#3498db',
                              help='Color en formato hex. Ej: #e74c3c, #2ecc71, #9b59b6')
    chart_color2 = fields.Char('Color secundario', default='#2ecc71',
                               help='Segundo color para barras horizontales o degradados')
    chart_height = fields.Integer('Altura gráfica (px)', default=320)
    col_width = fields.Selection([
        ('100%',    'Ancho completo'),
        ('50%',     'Mitad (50%)'),
        ('33.33%',  'Un tercio (33%)'),
        ('25%',     'Un cuarto (25%)'),
    ], string='Ancho del widget', default='50%')

    # ── Opciones tabla ────────────────────────────────────────
    table_striped = fields.Boolean('Filas alternadas', default=True)
    table_max_rows = fields.Integer('Máximo de filas', default=500,
                                    help='0 = sin límite (hasta 5000)')
    table_header_color = fields.Char('Color cabecera tabla', default='#34495e')
    table_font_size = fields.Selection([
        ('11px', 'Pequeño'),
        ('13px', 'Normal'),
        ('15px', 'Grande'),
    ], string='Tamaño de texto tabla', default='13px')

    # ── Opciones barras ───────────────────────────────────────
    bar_orientation = fields.Selection([
        ('vertical',    'Vertical'),
        ('horizontal',  'Horizontal'),
    ], string='Orientación barras', default='vertical')
    bar_show_values = fields.Boolean('Mostrar valores en barras', default=True)
    bar_rounded = fields.Boolean('Bordes redondeados', default=True)
    bar_sort = fields.Selection([
        ('desc', 'Mayor a menor'),
        ('asc',  'Menor a mayor'),
        ('none', 'Sin ordenar'),
    ], string='Ordenar barras', default='desc')
    bar_max_items = fields.Integer('Máx. barras a mostrar', default=20,
                                   help='0 = todas')

    # ── Opciones línea ────────────────────────────────────────
    line_show_dots = fields.Boolean('Mostrar puntos', default=True)
    line_show_area = fields.Boolean('Área bajo la curva', default=True)
    line_smooth = fields.Boolean('Línea suavizada (curva)', default=False)
    line_stroke_width = fields.Selection([
        ('1.5', 'Fina'),
        ('2.5', 'Normal'),
        ('4',   'Gruesa'),
    ], string='Grosor de línea', default='2.5')

    # ── Opciones torta ────────────────────────────────────────
    pie_donut = fields.Boolean('Torta tipo dona', default=False)
    pie_show_pct = fields.Boolean('Mostrar porcentaje', default=True)
    pie_show_value = fields.Boolean('Mostrar valor absoluto', default=False)
    pie_max_slices = fields.Integer('Máx. sectores', default=12,
                                    help='El resto se agrupa en "Otros"')

    # ── Opciones KPI ──────────────────────────────────────────
    kpi_prefix = fields.Char('Prefijo', help='Ej: $ COP')
    kpi_suffix = fields.Char('Sufijo', help='Ej: unidades, kg, %')
    kpi_icon = fields.Char('Ícono (emoji)', help='Ej: 💰 📦 📈')
    kpi_bg_color = fields.Char('Color de fondo KPI', default='#ffffff')
    kpi_compare_field_id = fields.Many2one(
        'nf.intelligence.widget.column',
        string='Segunda columna (comparación)',
        domain="[('widget_id', '=', id)]",
        ondelete='set null',
        help='Columna para mostrar una barra de progreso comparativa',
    )

    # ── Opciones pivot ────────────────────────────────────────
    pivot_show_totals = fields.Boolean('Mostrar totales', default=True)
    pivot_header_color = fields.Char('Color cabecera pivot', default='#2c3e50')
    pivot_max_rows = fields.Integer('Máx. filas pivot', default=200)

    # ── Línea de meta/objetivo (barras y líneas) ──────────────
    target_value = fields.Float(
        'Valor objetivo / meta', default=0.0,
        help='Dibuja una línea roja punteada de meta en la gráfica. 0 = desactivado',
    )
    target_label = fields.Char(
        'Etiqueta de meta', default='Meta',
        help='Texto junto a la línea de meta. Ej: Presupuesto, Cuota, Límite',
    )

    # ── Formato condicional para tabla ────────────────────────
    table_cond_enable = fields.Boolean(
        'Activar formato condicional', default=False,
        help='Colorea automáticamente una columna numérica según umbrales',
    )
    table_cond_col = fields.Char(
        'Columna a colorear',
        help='Nombre de la columna (tal como aparece en Columnas detectadas, sin distinción de mayúsculas)',
    )
    table_cond_low = fields.Float(
        'Umbral rojo (menor que)', default=0.0,
        help='Valores por debajo de este número → rojo',
    )
    table_cond_mid = fields.Float(
        'Umbral amarillo (menor que)', default=0.0,
        help='Valores entre umbral rojo y éste → amarillo. Por encima → verde',
    )

    # ── Filtros ───────────────────────────────────────────────
    filter_ids = fields.One2many(
        'nf.intelligence.widget.filter', 'widget_id', 'Filtros activos'
    )

    @api.onchange('report_id')
    def _onchange_report_id(self):
        """Rebuild param table and clear column state when report changes."""
        self._clear_col_state()
        if not self.report_id:
            self.widget_param_ids = [(5, 0, 0)]
            return
        today = str(fields.Date.today())
        new_params = []
        for p in self.report_id.param_ids:
            ptype = getattr(p, 'param_type', 'char')
            val = today if ptype == 'date' else ('0' if ptype in ('integer', 'float') else '')
            new_params.append((0, 0, {'name': p.name, 'param_type': ptype, 'value_input': val}))
        self.widget_param_ids = [(5, 0, 0)] + new_params

    def _clear_col_state(self):
        self.detected_columns = ''
        self.label_field = ''
        self.value_field = ''
        self.col_field = ''
        self.label_field_id = False
        self.value_field_id = False
        self.col_field_id = False
        self.preview_html = False

    @api.onchange('label_field_id')
    def _onchange_label_field_id(self):
        if self.label_field_id:
            self.label_field = self.label_field_id.name

    @api.onchange('value_field_id')
    def _onchange_value_field_id(self):
        if self.value_field_id:
            self.value_field = self.value_field_id.name

    @api.onchange('col_field_id')
    def _onchange_col_field_id(self):
        if self.col_field_id:
            self.col_field = self.col_field_id.name

    def action_detect_columns(self):
        """Execute SQL, detect column types via pg OIDs, auto-assign label/value."""
        self.ensure_one()
        if not self.report_id:
            return self._notif('Sin reporte', 'Seleccione un reporte primero.', 'warning')
        raw = self._resolve_params()
        # PostgreSQL numeric type OIDs: int2/4/8, float4/8, numeric
        NUMERIC_OIDS = {20, 21, 23, 700, 701, 1700}
        try:
            self.env.cr.execute(self.report_id.query, raw)
            desc = self.env.cr.description or []
            col_info = [(d[0], d[1]) for d in desc]
            rows = self.env.cr.fetchmany(5)
        except Exception as exc:
            err = str(exc)[:500]
            self.write({'detected_columns': f'❌ Error:\n{err}', 'preview_html': False})
            return self._notif('Error al ejecutar SQL', err, 'danger', sticky=True)
        if not col_info:
            self.write({'detected_columns': 'La consulta no retornó columnas.'})
            return self._notif('Sin columnas', 'La consulta no retornó columnas.', 'warning')
        # Build summary with type badges
        lines = ['COLUMNAS DETECTADAS:']
        for i, (cname, coid) in enumerate(col_info, 1):
            icon = '🔢' if coid in NUMERIC_OIDS else '🔤'
            tipo = 'numérico' if coid in NUMERIC_OIDS else 'texto'
            lines.append(f'  {i}. {icon} {cname}  ({tipo})')
        if rows:
            lines.append('')
            lines.append('MUESTRA (5 filas):')
            widths = [max(len(c[0]), 8) for c in col_info]
            header = ' | '.join(c[0].ljust(w)[:w] for c, w in zip(col_info, widths))
            lines.append('  ' + header)
            lines.append('  ' + '-' * len(header))
            for row in rows:
                cells = [(str(v) if v is not None else 'NULL').ljust(w)[:w]
                         for v, w in zip(row, widths)]
                lines.append('  ' + ' | '.join(cells))
        # Rebuild column records with type info
        self.available_column_ids.unlink()
        col_records = self.env['nf.intelligence.widget.column'].create([
            {
                'widget_id': self.id,
                'name': cname,
                'position': i + 1,
                'col_type': 'numeric' if coid in NUMERIC_OIDS else 'text',
            }
            for i, (cname, coid) in enumerate(col_info)
        ])
        self.write({
            'detected_columns': '\n'.join(lines),
            'label_field': False,
            'value_field': False,
            'col_field': False,
            'label_field_id': False,
            'value_field_id': False,
            'col_field_id': False,
            'preview_html': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configurar Widget',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_preview(self):
        """Render this widget with live data and refresh the form to show the preview."""
        self.ensure_one()
        import html as html_lib
        if not self.report_id:
            return self._notif('Sin reporte', 'Seleccione un reporte primero.', 'warning')
        viewer = self.env['nf.intelligence.viewer'].create({
            'dashboard_id': self.dashboard_id.id,
        })
        rows, cols, error = viewer._execute(self)
        if error:
            content = (
                '<div style="background:#fdf2f2;border:1px solid #e74c3c;color:#c0392b;'
                'padding:12px;border-radius:4px;">'
                f'<b>Error SQL:</b> {html_lib.escape(str(error))}</div>'
            )
        elif not rows:
            content = (
                '<div style="color:#aaa;padding:24px;font-size:14px;text-align:center;">'
                'Sin datos para los parámetros configurados.</div>'
            )
        else:
            rows = viewer._filter(rows, cols, self.filter_ids)
            if not rows:
                content = (
                    '<div style="color:#aaa;padding:24px;font-size:14px;text-align:center;">'
                    'Sin datos tras aplicar los filtros.</div>'
                )
            else:
                dispatch = {
                    'table': viewer._render_table, 'bar':   viewer._render_bar,
                    'line':  viewer._render_line,  'pie':   viewer._render_pie,
                    'pivot': viewer._render_pivot, 'kpi':   viewer._render_kpi,
                }
                fn = dispatch.get(self.widget_type, viewer._render_table)
                content = fn(self, rows, cols)
        preview = (
            viewer._css()
            + '<div class="nf-dash" style="padding:0;">'
            + '<div class="nf-widget" style="width:100%;margin:0;min-width:0;">'
            + f'<div class="nf-whead">{html_lib.escape(self.name)}</div>'
            + f'<div class="nf-wbody">{content}</div>'
            + '</div></div>'
        )
        viewer.unlink()
        self.write({'preview_html': preview})
        return {
            'type': 'ir.actions.act_window',
            'name': f'Vista previa — {self.name}',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _resolve_params(self):
        """Return params dict: prefer widget_param_ids table, fallback to JSON."""
        if self.widget_param_ids:
            return {p.name: p.get_value() for p in self.widget_param_ids}
        try:
            return json.loads(self.param_vals or '{}')
        except Exception:
            return {}

    @staticmethod
    def _notif(title, message, ntype, sticky=False):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': title, 'message': message, 'type': ntype, 'sticky': sticky},
        }

    @api.depends('report_id', 'report_id.param_ids')
    def _compute_report_param_names(self):
        for rec in self:
            if rec.report_id and rec.report_id.param_ids:
                names = [f'"{p.name}"' for p in rec.report_id.param_ids]
                rec.report_param_names = ', '.join(names)
            else:
                rec.report_param_names = 'Sin parámetros — use {}'


class NfIntelligenceWidgetFilter(models.Model):
    _name = 'nf.intelligence.widget.filter'
    _description = 'Filtro de Widget NF Intelligence'
    _order = 'sequence, id'

    widget_id = fields.Many2one(
        'nf.intelligence.widget', ondelete='cascade', required=True
    )
    sequence = fields.Integer('Sec.', default=10)
    column_name = fields.Char('Columna SQL', required=True,
                              help='Nombre exacto de la columna del resultado SQL')
    operator = fields.Selection([
        ('=',           '= Igual a'),
        ('!=',          '≠ Distinto de'),
        ('>',           '> Mayor que'),
        ('<',           '< Menor que'),
        ('>=',          '≥ Mayor o igual'),
        ('<=',          '≤ Menor o igual'),
        ('contains',     '∋ Contiene'),
        ('not_contains', '∌ No contiene'),
    ], string='Operador', required=True, default='=')
    value = fields.Char('Valor', required=True)


class NfIntelligenceWidgetColumn(models.Model):
    _name = 'nf.intelligence.widget.column'
    _description = 'Columna detectada de Widget NF Intelligence'
    _order = 'position, id'

    widget_id = fields.Many2one(
        'nf.intelligence.widget', ondelete='cascade', required=True
    )
    name = fields.Char('Columna', required=True)
    position = fields.Integer(default=10)
    col_type = fields.Selection([
        ('text',    'Texto'),
        ('numeric', 'Numérico'),
    ], string='Tipo', default='text')

    def name_get(self):
        icon = {'numeric': '🔢 ', 'text': '🔤 '}
        return [(r.id, icon.get(r.col_type, '') + r.name) for r in self]


class NfIntelligenceWidgetParam(models.Model):
    _name = 'nf.intelligence.widget.param'
    _description = 'Parámetro de Widget NF Intelligence'
    _order = 'sequence, id'

    widget_id = fields.Many2one(
        'nf.intelligence.widget', ondelete='cascade', required=True
    )
    sequence = fields.Integer(default=10)
    name = fields.Char('Parámetro', required=True)
    param_type = fields.Selection([
        ('date',     'Fecha'),
        ('datetime', 'Fecha y hora'),
        ('integer',  'Número entero'),
        ('float',    'Decimal'),
        ('char',     'Texto'),
    ], string='Tipo', default='char')
    value_input = fields.Char(
        'Valor',
        help='Use formato YYYY-MM-DD para fechas. Ej: 2026-01-15',
    )

    def get_value(self):
        self.ensure_one()
        v = self.value_input or ''
        if self.param_type == 'date':
            try:
                return fields.Date.from_string(v)
            except Exception:
                return None
        if self.param_type == 'datetime':
            try:
                return fields.Datetime.from_string(v)
            except Exception:
                return None
        if self.param_type == 'integer':
            try:
                return int(v)
            except (ValueError, TypeError):
                return 0
        if self.param_type == 'float':
            try:
                return float(v.replace(',', '.'))
            except (ValueError, TypeError):
                return 0.0
        return v
