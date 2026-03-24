# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class NfSchemaBrowser(models.TransientModel):
    _name = 'nf.schema.browser'
    _description = 'Explorador de Esquema de Base de Datos'

    table_filter = fields.Char(
        'Buscar tabla',
        default='',
        help='Escriba parte del nombre de la tabla. Deje vacío para ver todas.'
    )
    column_filter = fields.Char(
        'Buscar campo',
        default='',
        help='Filtra también por nombre de campo. Deje vacío para ver todos.'
    )
    result_html = fields.Html('Resultado', readonly=True, sanitize=False)
    has_results = fields.Boolean(default=False)

    def action_search(self):
        self.ensure_one()
        table_f = (self.table_filter or '').strip()
        column_f = (self.column_filter or '').strip()

        # Añadir comodines si no los tiene
        table_sql = f'%{table_f}%' if table_f else '%'
        column_sql = f'%{column_f}%' if column_f else '%'

        try:
            self.env.cr.execute("""
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    COALESCE(c.character_maximum_length::text, ''),
                    c.is_nullable,
                    COALESCE(pgd.description, '')
                FROM information_schema.columns c
                LEFT JOIN pg_class pc
                       ON pc.relname = c.table_name AND pc.relkind = 'r'
                LEFT JOIN pg_description pgd
                       ON pgd.objoid = pc.oid
                      AND pgd.objsubid = c.ordinal_position
                WHERE c.table_schema = 'public'
                  AND c.table_name   ILIKE %s
                  AND c.column_name  ILIKE %s
                ORDER BY c.table_name, c.ordinal_position
                LIMIT 3000
            """, (table_sql, column_sql))
            rows = self.env.cr.fetchall()
        except Exception as exc:
            raise UserError(f'Error al consultar el esquema:\n{exc}')

        if not rows:
            self.write({
                'result_html': (
                    '<style>.nf-empty{font-family:Arial,sans-serif;padding:14px;'
                    'color:#888;font-size:13px;}</style>'
                    '<div class="nf-empty">No se encontraron tablas/campos con ese filtro.</div>'
                ),
                'has_results': True,
            })
            return self._reopen()

        # Agrupar por tabla
        tables = {}
        for tbl, col, dtype, maxlen, nullable, descr in rows:
            tables.setdefault(tbl, []).append((col, dtype, maxlen, nullable, descr))

        self.write({
            'result_html': self._build_schema_html(tables),
            'has_results': True,
        })
        return self._reopen()

    def _build_schema_html(self, tables):
        styles = """<style>
            .nf-sch { font-family: Arial, sans-serif; font-size: 12px; }
            .nf-sch h4 {
                background: #2c3e50; color: #fff;
                padding: 6px 12px; margin: 14px 0 0 0;
                border-radius: 4px 4px 0 0; font-size: 13px;
            }
            .nf-sch table {
                width: 100%; border-collapse: collapse; margin-bottom: 2px;
            }
            .nf-sch th {
                background: #34495e; color: #fff;
                padding: 4px 8px; text-align: left; font-weight: bold;
            }
            .nf-sch td { padding: 3px 8px; border-bottom: 1px solid #eee; }
            .nf-sch tr:nth-child(even) td { background: #f9f9f9; }
            .nf-sch .desc { color: #666; font-style: italic; }
            .nf-sch .footer {
                color: #888; font-size: 11px; padding: 8px 4px; margin-top: 8px;
            }
        </style>"""

        body = '<div class="nf-sch">'
        for tbl, columns in sorted(tables.items()):
            body += f'<h4>&#128196; {tbl}</h4>'
            body += (
                '<table><thead><tr>'
                '<th>Campo</th><th>Tipo de dato</th>'
                '<th>Long.</th><th>Nulo</th><th>Descripci&oacute;n</th>'
                '</tr></thead><tbody>'
            )
            for col, dtype, maxlen, nullable, descr in columns:
                body += (
                    f'<tr><td><b>{col}</b></td>'
                    f'<td>{dtype}</td>'
                    f'<td>{maxlen}</td>'
                    f'<td>{nullable}</td>'
                    f'<td class="desc">{descr}</td></tr>'
                )
            body += '</tbody></table>'

        total_cols = sum(len(v) for v in tables.values())
        body += (
            f'<div class="footer">'
            f'Se encontraron <b>{len(tables)}</b> tabla(s) y '
            f'<b>{total_cols}</b> campo(s).</div>'
        )
        body += '</div>'
        return styles + body

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
