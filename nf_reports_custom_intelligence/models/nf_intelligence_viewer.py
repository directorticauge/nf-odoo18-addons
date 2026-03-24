# -*- coding: utf-8 -*-
import json
import math
import colorsys
import html as html_lib
from collections import defaultdict

from odoo import models, fields


class NfIntelligenceViewer(models.TransientModel):
    _name = 'nf.intelligence.viewer'
    _description = 'Visor de Dashboard NF Intelligence'

    dashboard_id = fields.Many2one(
        'nf.intelligence.dashboard', 'Dashboard', required=True
    )
    result_html = fields.Html('Contenido', readonly=True, sanitize=False)
    last_rendered = fields.Datetime('Última actualización', readonly=True)

    # ── Render principal ──────────────────────────────────────────────────────

    def action_render(self):
        self.ensure_one()
        widgets = self.dashboard_id.widget_ids.sorted('sequence')
        if not widgets:
            self.result_html = (
                '<div style="padding:24px;color:#888;font-family:Arial,sans-serif;">'
                'No hay widgets configurados en este dashboard.</div>'
            )
            return self._reopen()

        parts = [self._css()]
        parts.append('<div class="nf-dash">')
        for w in widgets:
            parts.append(self._render_widget(w))
        parts.append('</div>')

        self.write({
            'result_html': ''.join(parts),
            'last_rendered': fields.Datetime.now(),
        })
        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ── Widget dispatcher ────────────────────────────────────────────────────

    def _render_widget(self, w):
        width = w.col_width or '50%'
        rows, cols, error = self._execute(w)

        if error:
            content = (
                '<div class="nf-err"><b>Error SQL:</b> '
                f'{html_lib.escape(str(error))}</div>'
            )
        elif not rows:
            content = (
                '<div class="nf-empty">Sin datos para los parámetros configurados.</div>'
            )
        else:
            rows = self._filter(rows, cols, w.filter_ids)
            if not rows:
                content = (
                    '<div class="nf-empty">Sin datos tras aplicar los filtros.</div>'
                )
            else:
                dispatch = {
                    'table':  self._render_table,
                    'bar':    self._render_bar,
                    'line':   self._render_line,
                    'pie':    self._render_pie,
                    'pivot':  self._render_pivot,
                    'kpi':    self._render_kpi,
                    'matrix': self._render_matrix,
                }
                fn = dispatch.get(w.widget_type, self._render_table)
                content = fn(w, rows, cols)

        return (
            f'<div class="nf-widget" style="width:calc({width} - 12px);min-width:260px;">'
            f'<div class="nf-whead">{html_lib.escape(w.name)}</div>'
            f'<div class="nf-wbody">{content}</div>'
            f'</div>'
        )

    # ── SQL execution ────────────────────────────────────────────────────────

    def _execute(self, widget):
        # Prefer structured param table; fallback to legacy JSON
        if getattr(widget, 'widget_param_ids', None):
            raw = {p.name: p.get_value() for p in widget.widget_param_ids}
        else:
            try:
                raw = json.loads(widget.param_vals or '{}')
            except Exception:
                raw = {}

        from odoo.fields import Date as ODate, Datetime as ODT
        params = {}
        for k, v in raw.items():
            if isinstance(v, str) and len(v) == 10:
                try:
                    params[k] = ODate.from_string(v)
                    continue
                except Exception:
                    pass
            if isinstance(v, str) and len(v) == 19:
                try:
                    params[k] = ODT.from_string(v)
                    continue
                except Exception:
                    pass
            params[k] = v

        try:
            self.env.cr.execute(widget.report_id.query, params)
            rows = self.env.cr.fetchall()
            cols = [d[0] for d in (self.env.cr.description or [])]
            return rows, cols, None
        except Exception as exc:
            return [], [], exc

    # ── Filters ──────────────────────────────────────────────────────────────

    def _filter(self, rows, cols, filters):
        if not filters:
            return rows
        idx = {c: i for i, c in enumerate(cols)}
        for f in filters:
            if f.column_name not in idx:
                continue
            i = idx[f.column_name]
            op = f.operator
            val = f.value
            out = []
            for row in rows:
                cell = row[i]
                try:
                    cn = float(str(cell or '0').replace(',', '.'))
                    vn = float(val.replace(',', '.'))
                    match = (
                        (op == '='  and cn == vn) or
                        (op == '!=' and cn != vn) or
                        (op == '>'  and cn >  vn) or
                        (op == '<'  and cn <  vn) or
                        (op == '>=' and cn >= vn) or
                        (op == '<=' and cn <= vn)
                    )
                    if match:
                        out.append(row)
                    continue
                except (ValueError, TypeError):
                    pass
                cs = str(cell or '').lower()
                vs = val.lower()
                if   op == '='           and cs == vs:        out.append(row)
                elif op == '!='          and cs != vs:        out.append(row)
                elif op == 'contains'    and vs in cs:        out.append(row)
                elif op == 'not_contains'and vs not in cs:    out.append(row)
            rows = out
        return rows

    # ── TABLE ────────────────────────────────────────────────────────────────

    def _render_table(self, w, rows, cols):
        max_rows = w.table_max_rows or 500
        if max_rows <= 0:
            max_rows = 5000
        display = rows[:max_rows]
        hcolor = w.table_header_color or '#34495e'
        fsize = w.table_font_size or '13px'
        striped = w.table_striped

        heads = ''.join(
            f'<th style="background:{hcolor};color:#fff;padding:7px 10px;'
            f'text-align:left;white-space:nowrap;position:sticky;top:0;font-size:{fsize};">'
            f'{html_lib.escape(c)}</th>'
            for c in cols
        )
        cond_enable = w.table_cond_enable
        cond_col = (w.table_cond_col or '').strip().lower()
        cond_low = w.table_cond_low
        cond_mid = w.table_cond_mid
        cond_idx = None
        if cond_enable and cond_col:
            cond_idx = next((i for i, c in enumerate(cols) if c.lower() == cond_col), None)

        body = ''
        for idx, row in enumerate(display):
            bg = '#f8f9fa' if (striped and idx % 2 == 1) else '#fff'
            cells = ''
            for j, v in enumerate(row):
                cell_style = f'padding:5px 10px;border-bottom:1px solid #eee;font-size:{fsize};'
                if cond_idx is not None and j == cond_idx:
                    try:
                        cv = float(str(v).replace(',', '.')) if v is not None else 0.0
                        if cv < cond_low:
                            cell_style += 'background:#fde8e8;color:#c0392b;font-weight:bold;'
                        elif cv < cond_mid:
                            cell_style += 'background:#fef9e7;color:#b7950b;font-weight:bold;'
                        else:
                            cell_style += 'background:#eafaf1;color:#1e8449;font-weight:bold;'
                    except (ValueError, TypeError):
                        pass
                cells += (
                    f'<td style="{cell_style}">'
                    f'{html_lib.escape(str(v) if v is not None else "")}</td>'
                )
            body += f'<tr style="background:{bg};">{cells}</tr>'
        total = len(rows)
        note = (
            f'<div class="nf-note">{total} fila(s)'
            + (f' — mostrando primeras {max_rows}' if total > max_rows else '')
            + '</div>'
        )
        return (
            f'<div style="overflow:auto;max-height:480px;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr>{heads}</tr></thead>'
            f'<tbody>{body}</tbody></table>'
            f'</div>{note}'
        )

    # ── BAR ──────────────────────────────────────────────────────────────────

    def _render_bar(self, w, rows, cols):
        labels, values = self._agg(w, rows, cols)
        if not labels:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(w.value_field or '(sin configurar)')
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )

        # Sort
        sort_mode = w.bar_sort or 'desc'
        if sort_mode == 'desc':
            paired = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        elif sort_mode == 'asc':
            paired = sorted(zip(labels, values), key=lambda x: x[1])
        else:
            paired = list(zip(labels, values))
        max_items = w.bar_max_items or 20
        if max_items > 0:
            paired = paired[:max_items]
        labels, values = [p[0] for p in paired], [p[1] for p in paired]

        h = w.chart_height or 320
        color = w.chart_color or '#3498db'
        color2 = w.chart_color2 or color
        show_vals = w.bar_show_values
        rounded = 3 if w.bar_rounded else 0
        horizontal = (w.bar_orientation == 'horizontal')

        W = 640
        if horizontal:
            PL, PR, PT, PB = 140, 60, 10, 22  # PB>=22 so tick labels at y=PT+CH+14 stay in viewBox
        else:
            PL, PR, PT, PB = 56, 16, 20, 88
        CW = W - PL - PR
        CH = h - PT - PB
        n = len(values)
        max_v = max(values) or 1

        bars = ticks = lbls = ''

        if horizontal:
            slot = CH / n
            bh = slot * 0.65
            gap_y = slot * 0.35

            for step in range(5):
                vt = max_v * step / 4
                xt = PL + (vt / max_v) * CW
                ticks += (
                    f'<line x1="{xt:.1f}" y1="{PT}" x2="{xt:.1f}" y2="{PT+CH}" '
                    f'stroke="#eee" stroke-width="1"/>'
                    f'<text x="{xt:.1f}" y="{PT+CH+14}" text-anchor="middle" '
                    f'font-size="9" fill="#999">{self._fmt(vt)}</text>'
                )

            # gradient: interpolate color → color2 by rank
            for i, (lbl, v) in enumerate(zip(labels, values)):
                bw_px = (v / max_v) * CW
                y = PT + i * slot + gap_y / 2
                # color blend
                t = i / max(n - 1, 1)
                fc = self._blend_hex(color, color2, t)
                bars += (
                    f'<rect x="{PL}" y="{y:.1f}" width="{bw_px:.1f}" '
                    f'height="{bh:.1f}" fill="{fc}" rx="{rounded}">'
                    f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)}</title></rect>'
                )
                if show_vals:
                    bars += (
                        f'<text x="{PL + bw_px + 4:.1f}" y="{y + bh/2 + 4:.1f}" '
                        f'font-size="9" fill="#555">{self._fmt(v)}</text>'
                    )
                lbl_s = (lbl[:18] + '…') if len(lbl) > 19 else lbl
                lbls += (
                    f'<text x="{PL - 4}" y="{y + bh/2 + 4:.1f}" text-anchor="end" '
                    f'font-size="9" fill="#555">{html_lib.escape(lbl_s)}</text>'
                )

            return (
                f'<svg viewBox="0 0 {W} {h}" style="width:100%;height:{h}px;">'
                f'<rect width="{W}" height="{h}" fill="#fafafa" rx="4"/>'
                f'{ticks}'
                f'<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{PT+CH}" stroke="#ccc"/>'
                f'<line x1="{PL}" y1="{PT+CH}" x2="{W-PR}" y2="{PT+CH}" stroke="#ccc"/>'
                f'{bars}{lbls}'
                f'</svg>'
            )
        else:
            bw = CW / n * 0.72
            gap = CW / n * 0.28

            for step in range(5):
                vt = max_v * step / 4
                yt = PT + CH - (vt / max_v) * CH
                ticks += (
                    f'<line x1="{PL}" y1="{yt:.1f}" x2="{W-PR}" y2="{yt:.1f}" '
                    f'stroke="#eee" stroke-width="1"/>'
                    f'<text x="{PL-4}" y="{yt+4:.1f}" text-anchor="end" '
                    f'font-size="9" fill="#999">{self._fmt(vt)}</text>'
                )

            for i, (lbl, v) in enumerate(zip(labels, values)):
                bh_px = max(0, (v / max_v) * CH)  # clamp negatives
                x = PL + i * (CW / n) + gap / 2
                y = PT + CH - bh_px
                cx_ = x + bw / 2
                t = i / max(n - 1, 1)
                fc = self._blend_hex(color, color2, t)
                bars += (
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                    f'height="{bh_px:.1f}" fill="{fc}" rx="{rounded}" opacity="0.9">'
                    f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)}</title></rect>'
                )
                if show_vals:
                    bars += (
                        f'<text x="{cx_:.1f}" y="{y-3:.1f}" text-anchor="middle" '
                        f'font-size="9" fill="#444">{self._fmt(v)}</text>'
                    )
                lbl_s = (lbl[:13] + '…') if len(lbl) > 14 else lbl
                lbls += (
                    f'<text x="{cx_:.1f}" y="{PT+CH+14:.1f}" text-anchor="end" '
                    f'font-size="9" fill="#666" '
                    f'transform="rotate(-35,{cx_:.1f},{PT+CH+14:.1f})">'
                    f'{html_lib.escape(lbl_s)}</text>'
                )

            return (
                f'<svg viewBox="0 0 {W} {h}" style="width:100%;height:{h}px;">'
                f'<rect width="{W}" height="{h}" fill="#fafafa" rx="4"/>'
                f'{ticks}'
                f'<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{PT+CH}" stroke="#ccc"/>'
                f'<line x1="{PL}" y1="{PT+CH}" x2="{W-PR}" y2="{PT+CH}" stroke="#ccc"/>'
                f'{bars}{lbls}'
                f'</svg>'
            )

    # ── LINE ─────────────────────────────────────────────────────────────────

    def _render_line(self, w, rows, cols):
        labels, values = self._agg(w, rows, cols)
        if not labels:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(w.value_field or '(sin configurar)')
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )
        if len(labels) < 2:
            return self._render_bar(w, rows, cols)
        h = w.chart_height or 320
        color = w.chart_color or '#3498db'
        stroke_w = w.line_stroke_width or '2.5'
        show_dots = w.line_show_dots
        show_area = w.line_show_area
        smooth = w.line_smooth
        W = 640
        PL, PR, PT, PB = 64, 20, 20, 88
        CW = W - PL - PR
        CH = h - PT - PB
        n = len(values)
        max_v = max(values) or 1
        min_v = min(values)
        rng = max_v - min_v
        if rng == 0:  # all values identical → center line at mid-height
            min_v = max_v - 1
            rng = 1

        def px(i, v):
            x = PL + i * CW / (n - 1)
            y = PT + CH - ((v - min_v) / rng) * CH
            return x, y

        pts = [px(i, v) for i, v in enumerate(values)]

        if smooth and n >= 3:
            # Catmull-Rom → cubic bezier
            d_parts = [f'M {pts[0][0]:.1f},{pts[0][1]:.1f}']
            for i in range(1, n):
                p0 = pts[max(i - 2, 0)]
                p1 = pts[i - 1]
                p2 = pts[i]
                p3 = pts[min(i + 1, n - 1)]
                cp1x = p1[0] + (p2[0] - p0[0]) / 6
                cp1y = p1[1] + (p2[1] - p0[1]) / 6
                cp2x = p2[0] - (p3[0] - p1[0]) / 6
                cp2y = p2[1] - (p3[1] - p1[1]) / 6
                d_parts.append(
                    f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {p2[0]:.1f},{p2[1]:.1f}'
                )
            path_d = ' '.join(d_parts)
            line_svg = (
                f'<path d="{path_d}" fill="none" stroke="{color}" '
                f'stroke-width="{stroke_w}" stroke-linejoin="round" stroke-linecap="round"/>'
            )
            if show_area:
                area_d = (
                    path_d +
                    f' L {pts[-1][0]:.1f},{PT+CH:.1f} L {PL:.1f},{PT+CH:.1f} Z'
                )
                line_svg = (
                    f'<path d="{area_d}" fill="{color}22"/>' + line_svg
                )
        else:
            polyline = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
            area_pts = (
                f'{PL:.1f},{PT+CH:.1f} ' + polyline +
                f' {pts[-1][0]:.1f},{PT+CH:.1f}'
            )
            line_svg = ''
            if show_area:
                line_svg += f'<polygon points="{area_pts}" fill="{color}22"/>'
            line_svg += (
                f'<polyline points="{polyline}" fill="none" stroke="{color}" '
                f'stroke-width="{stroke_w}" stroke-linejoin="round"/>'
            )

        ticks = x_lbls = dots = ''
        for step in range(5):
            vt = min_v + rng * step / 4
            _, yt = px(0, vt)
            ticks += (
                f'<line x1="{PL}" y1="{yt:.1f}" x2="{W-PR}" y2="{yt:.1f}" '
                f'stroke="#eee" stroke-width="1"/>'
                f'<text x="{PL-4}" y="{yt+4:.1f}" text-anchor="end" '
                f'font-size="9" fill="#999">{self._fmt(vt)}</text>'
            )
        for i, (lbl, (x_, y_)) in enumerate(zip(labels, pts)):
            if show_dots:
                dots += (
                    f'<circle cx="{x_:.1f}" cy="{y_:.1f}" r="4" fill="{color}" '
                    f'stroke="white" stroke-width="1.5">'
                    f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)}</title></circle>'
                )
            else:
                # invisible hit area so tooltip works even without visible dot
                dots += (
                    f'<circle cx="{x_:.1f}" cy="{y_:.1f}" r="6" fill="transparent">'
                    f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)}</title></circle>'
                )
            lbl_s = (lbl[:13] + '…') if len(lbl) > 14 else lbl
            x_lbls += (
                f'<text x="{x_:.1f}" y="{PT+CH+14:.1f}" text-anchor="end" '
                f'font-size="9" fill="#666" '
                f'transform="rotate(-35,{x_:.1f},{PT+CH+14:.1f})">'
                f'{html_lib.escape(lbl_s)}</text>'
            )

        target_v = w.target_value
        target_lbl = w.target_label or 'Meta'
        target_svg = ''
        if target_v:
            _, ty = px(0, target_v)
            if PT <= ty <= PT + CH:
                target_svg = (
                    f'<line x1="{PL}" y1="{ty:.1f}" x2="{W-PR}" y2="{ty:.1f}" '
                    f'stroke="#e74c3c" stroke-width="2" stroke-dasharray="6,4" opacity="0.85"/>'
                    f'<text x="{W-PR-2}" y="{ty-4:.1f}" text-anchor="end" '
                    f'font-size="9" fill="#e74c3c" font-weight="bold">'
                    f'\u25b6 {html_lib.escape(target_lbl)}: {self._fmt(target_v)}</text>'
                )
        return (
            f'<svg viewBox="0 0 {W} {h}" style="width:100%;height:{h}px;">'
            f'<rect width="{W}" height="{h}" fill="#fafafa" rx="4"/>'
            f'{ticks}'
            f'<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{PT+CH}" stroke="#ccc"/>'
            f'<line x1="{PL}" y1="{PT+CH}" x2="{W-PR}" y2="{PT+CH}" stroke="#ccc"/>'
            f'{line_svg}{dots}{x_lbls}{target_svg}'
            f'</svg>'
        )

    # ── PIE ──────────────────────────────────────────────────────────────────

    def _render_pie(self, w, rows, cols):
        labels, values = self._agg(w, rows, cols)
        if not labels:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(w.value_field or '(sin configurar)')
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )
        max_slices = w.pie_max_slices or 12
        items = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        if len(items) > max_slices:
            main = items[:max_slices - 1]
            others_val = sum(v for _, v in items[max_slices - 1:])
            main.append(('Otros', others_val))
            items = main
        if not items:
            return '<div class="nf-empty">Sin datos.</div>'
        # filter out non-positive values (would cause backward/zero arcs)
        items = [(l, v) for l, v in items if v > 0]
        if not items:
            return '<div class="nf-empty">Sin datos positivos para graficar.</div>'
        labels = [i[0] for i in items]
        values = [i[1] for i in items]

        h = w.chart_height or 320
        W = 600
        cx_ = W * 0.37
        cy_ = h / 2
        donut = w.pie_donut or False
        show_pct = w.pie_show_pct
        show_val = w.pie_show_value
        outer_r = min(h / 2 - 20, 140)
        inner_r = outer_r * 0.5 if donut else 0
        total = sum(values) or 1
        n = len(values)

        base_color = w.chart_color or '#3498db'
        try:
            r_h = int(base_color.lstrip('#')[0:2], 16) / 255
            g_h = int(base_color.lstrip('#')[2:4], 16) / 255
            b_h = int(base_color.lstrip('#')[4:6], 16) / 255
            base_hue, _, _ = colorsys.rgb_to_hsv(r_h, g_h, b_h)
        except Exception:
            base_hue = 0.6

        slices = legend = labels_svg = ''
        angle = -math.pi / 2

        for i, (lbl, v) in enumerate(zip(labels, values)):
            frac = v / total
            end = angle + 2 * math.pi * frac
            hue = (base_hue + i / n) % 1.0
            rc, gc, bc = colorsys.hsv_to_rgb(hue, 0.62, 0.90)
            sc = '#{:02x}{:02x}{:02x}'.format(int(rc*255), int(gc*255), int(bc*255))

            if n == 1:
                tip = f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)} (100%)</title>'
                if donut:
                    slices += (
                        f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{outer_r:.1f}" '
                        f'fill="{sc}" stroke="white" stroke-width="2">{tip}</circle>'
                        f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{inner_r:.1f}" '
                        f'fill="#fafafa"/>'
                    )
                else:
                    slices += (
                        f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{outer_r:.1f}" '
                        f'fill="{sc}" stroke="white" stroke-width="2">{tip}</circle>'
                    )
            else:
                x1 = cx_ + outer_r * math.cos(angle)
                y1 = cy_ + outer_r * math.sin(angle)
                x2 = cx_ + outer_r * math.cos(end)
                y2 = cy_ + outer_r * math.sin(end)
                large = 1 if frac > 0.5 else 0
                if donut:
                    ix1 = cx_ + inner_r * math.cos(end)
                    iy1 = cy_ + inner_r * math.sin(end)
                    ix2 = cx_ + inner_r * math.cos(angle)
                    iy2 = cy_ + inner_r * math.sin(angle)
                    d = (
                        f'M {x1:.1f} {y1:.1f} '
                        f'A {outer_r:.1f} {outer_r:.1f} 0 {large} 1 {x2:.1f} {y2:.1f} '
                        f'L {ix1:.1f} {iy1:.1f} '
                        f'A {inner_r:.1f} {inner_r:.1f} 0 {large} 0 {ix2:.1f} {iy2:.1f} Z'
                    )
                else:
                    d = (
                        f'M {cx_:.1f} {cy_:.1f} '
                        f'L {x1:.1f} {y1:.1f} '
                        f'A {outer_r:.1f} {outer_r:.1f} 0 {large} 1 {x2:.1f} {y2:.1f} Z'
                    )
                slices += (
                    f'<path d="{d}" fill="{sc}" stroke="white" stroke-width="2">'
                    f'<title>{html_lib.escape(lbl)} \u2014 {self._fmt(v)} ({frac*100:.1f}%)</title>'
                    f'</path>'
                )

                # label on slice if big enough
                if frac > 0.06:
                    mid_a = (angle + end) / 2
                    lr = (outer_r + inner_r) / 2 if donut else outer_r * 0.65
                    lx = cx_ + lr * math.cos(mid_a)
                    ly = cy_ + lr * math.sin(mid_a)
                    ltext = ''
                    if show_pct:
                        ltext += f'{frac*100:.0f}%'
                    if show_val:
                        ltext += (' ' if ltext else '') + self._fmt(v)
                    if ltext:
                        labels_svg += (
                            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                            f'dominant-baseline="middle" font-size="10" '
                            f'fill="white" font-weight="bold">{ltext}</text>'
                        )

            pct = frac * 100
            ly_leg = 24 + i * 22
            lbl_s = (lbl[:22] + '…') if len(lbl) > 23 else lbl
            legend_text = html_lib.escape(lbl_s)
            if show_pct:
                legend_text += f' ({pct:.1f}%)'
            if show_val:
                legend_text += f' — {self._fmt(v)}'
            legend += (
                f'<rect x="{W*0.67:.0f}" y="{ly_leg-11}" width="13" height="13" '
                f'fill="{sc}" rx="3"/>'
                f'<text x="{W*0.67+18:.0f}" y="{ly_leg}" font-size="11" fill="#333">'
                f'{legend_text}</text>'
            )
            angle = end

        return (
            f'<svg viewBox="0 0 {W} {h}" style="width:100%;height:{h}px;">'
            f'<rect width="{W}" height="{h}" fill="#fafafa" rx="4"/>'
            f'{slices}{labels_svg}{legend}'
            f'</svg>'
        )

    # ── PIVOT ────────────────────────────────────────────────────────────────

    def _render_pivot(self, w, rows, cols):
        label_f = w.label_field or (w.label_field_id.name if w.label_field_id else '')
        value_f = w.value_field or (w.value_field_id.name if w.value_field_id else '')
        col_f = w.col_field or (w.col_field_id.name if w.col_field_id else '')
        ri, _ = self._col_idx(cols, label_f, 0)
        ci, ci_found = self._col_idx(cols, col_f, -1)
        ci = ci if (col_f and ci_found) else None
        vi, vi_found = self._col_idx(cols, value_f, len(cols) - 1)
        if not vi_found:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(value_f or '(sin configurar)')
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )
        func = w.agg_func or 'sum'
        show_totals = w.pivot_show_totals
        hcolor = w.pivot_header_color or '#2c3e50'
        max_rows = w.pivot_max_rows or 200

        agg = defaultdict(lambda: defaultdict(float))
        counts = defaultdict(lambda: defaultdict(int))
        mins = defaultdict(lambda: defaultdict(lambda: None))
        maxs = defaultdict(lambda: defaultdict(lambda: None))
        row_keys = []
        col_keys = []

        for row in rows:
            rk = str(row[ri] if row[ri] is not None else '')
            ck = str(row[ci] if (ci is not None and row[ci] is not None) else '—')
            try:
                v = float(str(row[vi]).replace(',', '.')) if row[vi] is not None else 0.0
            except (ValueError, TypeError):
                v = 0.0
            if rk not in row_keys:
                row_keys.append(rk)
            if ck not in col_keys:
                col_keys.append(ck)
            agg[rk][ck] += v
            counts[rk][ck] += 1
            if mins[rk][ck] is None or v < mins[rk][ck]:
                mins[rk][ck] = v
            if maxs[rk][ck] is None or v > maxs[rk][ck]:
                maxs[rk][ck] = v

        row_keys = row_keys[:max_rows]

        def agg_val(rk, ck):
            a = agg[rk][ck]
            c = counts[rk][ck]
            if func == 'avg':  return a / c if c else 0
            if func == 'count': return float(c)
            if func == 'min':  return mins[rk][ck] or 0
            if func == 'max':  return maxs[rk][ck] or 0
            return a

        th_style = (
            f'background:{hcolor};color:#fff;padding:6px 10px;'
            f'text-align:center;white-space:nowrap;position:sticky;top:0;'
        )
        row_hdr = label_f or cols[ri]
        col_heads = ''.join(
            f'<th style="{th_style}">{html_lib.escape(c)}</th>' for c in col_keys
        )
        total_th = f'<th style="{th_style}">Total</th>' if show_totals else ''
        header = (
            f'<tr>'
            f'<th style="{th_style}text-align:left;">{html_lib.escape(row_hdr)}</th>'
            f'{col_heads}{total_th}'
            f'</tr>'
        )

        body = ''
        col_totals = defaultdict(float)
        grand = 0.0
        row_th_style = (
            f'text-align:left;background:#ecf0f1;font-weight:normal;'
            f'padding:5px 10px;white-space:nowrap;'
        )

        for rk in row_keys:
            row_total = 0.0
            cells = ''
            for ck in col_keys:
                v = agg_val(rk, ck)
                cells += f'<td style="text-align:right;padding:4px 10px;border:1px solid #eee;">{self._fmt(v)}</td>'
                col_totals[ck] += v
                row_total += v
            grand += row_total
            row_total_td = (
                f'<td style="font-weight:bold;background:#fef9e7;text-align:right;padding:4px 10px;">'
                f'{self._fmt(row_total)}</td>'
            ) if show_totals else ''
            body += (
                f'<tr>'
                f'<th style="{row_th_style}">{html_lib.escape(rk)}</th>'
                f'{cells}{row_total_td}'
                f'</tr>'
            )

        if show_totals:
            total_cells = ''.join(
                f'<td style="font-weight:bold;background:#fef9e7;text-align:right;padding:4px 10px;">'
                f'{self._fmt(col_totals[ck])}</td>'
                for ck in col_keys
            )
            body += (
                f'<tr style="background:#d5e8d4;">'
                f'<th style="text-align:left;padding:5px 10px;">Gran Total</th>'
                f'{total_cells}'
                f'<td style="font-weight:bold;text-align:right;padding:4px 10px;">{self._fmt(grand)}</td>'
                f'</tr>'
            )

        func_lbl = dict(w._fields['agg_func'].selection).get(func, func)
        note = (
            f'<div class="nf-note">'
            f'{len(row_keys)} fila(s) × {len(col_keys)} col(s) — {func_lbl}'
            + (f' — mostrando primeros {max_rows}' if len(row_keys) >= max_rows else '')
            + '</div>'
        )
        return (
            f'<div style="overflow:auto;max-height:520px;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;">'
            f'<thead>{header}</thead><tbody>{body}</tbody>'
            f'</table></div>{note}'
        )

    # ── KPI ──────────────────────────────────────────────────────────────────

    def _render_kpi(self, w, rows, cols):
        value_f = w.value_field or (w.value_field_id.name if w.value_field_id else '')
        vi, vi_found = self._col_idx(cols, value_f, 0)
        if not vi_found:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(value_f or '(sin configurar)')
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )
        func = w.agg_func or 'sum'
        color = w.chart_color or '#2c3e50'
        bg = w.kpi_bg_color or '#ffffff'
        prefix = w.kpi_prefix or ''
        suffix = w.kpi_suffix or ''
        icon = w.kpi_icon or ''

        nums = []
        for row in rows:
            try:
                nums.append(float(str(row[vi]).replace(',', '.')) if row[vi] is not None else 0.0)
            except (ValueError, TypeError):
                pass

        result = 0.0
        if nums:
            if func == 'sum':    result = sum(nums)
            elif func == 'count': result = float(len(nums))
            elif func == 'avg':  result = sum(nums) / len(nums)
            elif func == 'min':  result = min(nums)
            elif func == 'max':  result = max(nums)
            else:                result = sum(nums)

        func_lbl = {
            'sum': 'Total', 'count': 'Conteo', 'avg': 'Promedio',
            'min': 'Mínimo', 'max': 'Máximo',
        }.get(func, func)
        field_lbl = value_f or (cols[vi] if vi < len(cols) else 'Valor')
        formatted = f'{prefix}{self._fmt(result)}{suffix}'

        # optional comparison bar
        compare_html = ''
        cfield = w.kpi_compare_field_id
        ci2, cfound = self._col_idx(cols, cfield.name if cfield else None, -1)
        if cfield and cfound:
            comp_nums = []
            for row in rows:
                try:
                    comp_nums.append(float(str(row[ci2] or 0).replace(',', '.')))
                except (ValueError, TypeError):
                    pass
            if comp_nums:
                comp_val = sum(comp_nums) if func == 'sum' else (
                    float(len(comp_nums)) if func == 'count' else sum(comp_nums) / len(comp_nums)
                )
                pct = min((result / comp_val * 100) if comp_val else 0, 100)
                compare_html = (
                    f'<div style="margin:10px auto;max-width:240px;">'
                    f'<div style="background:#eee;border-radius:6px;height:10px;">'
                    f'<div style="width:{pct:.1f}%;background:{color};height:10px;'
                    f'border-radius:6px;transition:width .3s;"></div></div>'
                    f'<div style="font-size:10px;color:#aaa;margin-top:3px;text-align:center;">'
                    f'{pct:.1f}% de {html_lib.escape(cfield.name)}: {self._fmt(comp_val)}'
                    f'</div></div>'
                )

        return (
            f'<div style="text-align:center;padding:24px 16px;background:{bg};border-radius:4px;">'
            f'<div style="font-size:36px;line-height:1;">{html_lib.escape(icon)}</div>'
            f'<div style="font-size:42px;font-weight:bold;color:{color};line-height:1.1;margin-top:6px;">'
            f'{html_lib.escape(formatted)}</div>'
            f'<div style="font-size:13px;color:#666;margin-top:8px;">'
            f'{func_lbl} de <b>{html_lib.escape(str(field_lbl))}</b></div>'
            f'{compare_html}'
            f'<div style="font-size:11px;color:#bbb;margin-top:6px;">'
            f'{len(rows)} registro(s)</div>'
            f'</div>'
        )

    # ── MATRIX (Mapa de Calor) ──────────────────────────────────────────────

    def _render_matrix(self, w, rows, cols):
        label_f = w.label_field or (w.label_field_id.name if w.label_field_id else '')
        value_f = w.value_field or (w.value_field_id.name if w.value_field_id else '')
        col_f   = w.col_field   or (w.col_field_id.name   if w.col_field_id   else '')

        if not value_f:
            return '<div class="nf-err">Configure el <b>Campo Valor</b> para el mapa de calor.</div>'

        ri, _       = self._col_idx(cols, label_f, 0)
        vi, vfound  = self._col_idx(cols, value_f, -1)
        if not vfound:
            return (
                '<div class="nf-err">No se encontró la columna de valor <b>'
                + html_lib.escape(value_f)
                + '</b>. Verifique el nombre exacto de la columna detectada.</div>'
            )
        ci, cfound = self._col_idx(cols, col_f, -1)
        ci = ci if (col_f and cfound) else None

        func     = w.agg_func or 'sum'
        show_val = w.bar_show_values
        max_rows = w.pivot_max_rows or 200
        hcolor   = w.pivot_header_color or '#2c3e50'
        color    = w.chart_color or '#3498db'

        agg       = defaultdict(lambda: defaultdict(float))
        counts    = defaultdict(lambda: defaultdict(int))
        cell_vals = defaultdict(lambda: defaultdict(list))
        row_keys  = []
        col_keys  = []

        for row in rows:
            rk = str(row[ri] if row[ri] is not None else '')
            ck = str(row[ci] if (ci is not None and row[ci] is not None) else '—')
            try:
                v = float(str(row[vi]).replace(',', '.')) if row[vi] is not None else 0.0
            except (ValueError, TypeError):
                v = 0.0
            if rk not in row_keys:
                row_keys.append(rk)
            if ck not in col_keys:
                col_keys.append(ck)
            agg[rk][ck] += v
            counts[rk][ck] += 1
            cell_vals[rk][ck].append(v)

        row_keys = row_keys[:max_rows]

        def get_val(rk, ck):
            a = agg[rk][ck]
            c = counts[rk][ck]
            cv = cell_vals[rk][ck]
            if func == 'avg':   return a / c if c else 0.0
            if func == 'count': return float(c)
            if func == 'min':   return min(cv) if cv else 0.0
            if func == 'max':   return max(cv) if cv else 0.0
            return a

        all_vals = [get_val(rk, ck) for rk in row_keys for ck in col_keys]
        max_v = max(all_vals) if all_vals else 1.0
        if max_v <= 0:
            max_v = 1.0

        th = (
            f'background:{hcolor};color:#fff;padding:5px 10px;'
            f'text-align:center;white-space:nowrap;font-size:11px;'
        )
        row_th = (
            'background:#ecf0f1;text-align:left;padding:4px 10px;'
            'white-space:nowrap;font-size:11px;font-weight:normal;border:1px solid #fff;'
        )

        col_heads = ''.join(
            f'<th style="{th}">{html_lib.escape(str(c)[:24])}</th>' for c in col_keys
        )
        header = (
            f'<tr>'
            f'<th style="{th}text-align:left;">'
            f'{html_lib.escape((label_f or cols[ri])[:24])}</th>'
            f'{col_heads}</tr>'
        )

        body = ''
        for rk in row_keys:
            cells = f'<th style="{row_th}">{html_lib.escape(str(rk)[:32])}</th>'
            for ck in col_keys:
                v = get_val(rk, ck)
                intensity = max(0.0, min(1.0, v / max_v))
                bg = self._blend_hex('#f4f4f4', color, intensity)
                text_color = '#fff' if intensity > 0.55 else '#333'
                label_tip = f'{html_lib.escape(rk)} / {html_lib.escape(ck)}: {self._fmt(v)}'
                cell_content = self._fmt(v) if show_val else ''
                cells += (
                    f'<td style="background:{bg};color:{text_color};'
                    f'text-align:center;padding:5px 8px;border:1px solid #fff;'
                    f'font-size:11px;min-width:55px;" title="{label_tip}">'
                    f'{cell_content}</td>'
                )
            body += f'<tr>{cells}</tr>'

        # Gradient legend
        steps = 6
        swatches = ''.join(
            f'<span style="display:inline-block;width:34px;height:12px;'
            f'background:{self._blend_hex("#f4f4f4", color, i/(steps-1))};'
            f'border:1px solid #ddd;"></span>'
            for i in range(steps)
        )
        legend = (
            f'<div style="margin-top:8px;font-size:10px;color:#888;'
            f'display:flex;align-items:center;gap:4px;">'
            f'<span>0</span>{swatches}<span>{self._fmt(max_v)}</span></div>'
        )

        func_lbl = dict(w._fields['agg_func'].selection).get(func, func)
        note = (
            f'<div class="nf-note">'
            f'{len(row_keys)} fila(s) × {len(col_keys)} columna(s) — {func_lbl}'
            + (f' — primeras {max_rows}' if len(row_keys) >= max_rows else '')
            + '</div>'
        )
        return (
            f'<div style="overflow:auto;max-height:520px;">'
            f'<table style="border-collapse:collapse;font-size:11px;">'
            f'<thead>{header}</thead><tbody>{body}</tbody>'
            f'</table></div>{legend}{note}'
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _agg(self, w, rows, cols):
        # Fallback: if Char field empty, read from the Many2one selector
        label_f = w.label_field or (w.label_field_id.name if w.label_field_id else '')
        value_f = w.value_field or (w.value_field_id.name if w.value_field_id else '')
        col_map = {c: i for i, c in enumerate(cols)}
        col_map_ci = {c.lower(): i for i, c in enumerate(cols)}  # case-insensitive

        def resolve(field_name, default_idx):
            if not field_name:
                return default_idx, None
            if field_name in col_map:
                return col_map[field_name], None
            ci = col_map_ci.get(field_name.lower())
            if ci is not None:
                return ci, None
            return default_idx, field_name  # not found → return name for error

        li, label_err = resolve(label_f, 0)
        vi, value_err = resolve(value_f, None)

        if value_err is not None or vi is None:
            return [], []  # caller will show nf-empty

        func = w.agg_func or 'sum'

        agg = defaultdict(float)
        counts = defaultdict(int)
        mins = {}
        maxs = {}

        for row in rows:
            lbl = str(row[li] if row[li] is not None else '')
            try:
                v = float(str(row[vi]).replace(',', '.')) if row[vi] is not None else 0.0
            except (ValueError, TypeError):
                v = 0.0
            agg[lbl] += v
            counts[lbl] += 1
            if lbl not in mins or v < mins[lbl]:
                mins[lbl] = v
            if lbl not in maxs or v > maxs[lbl]:
                maxs[lbl] = v

        if func == 'avg':
            data = {k: (agg[k] / counts[k] if counts[k] else 0) for k in agg}
        elif func == 'count':
            data = {k: float(counts[k]) for k in counts}
        elif func == 'min':
            data = mins
        elif func == 'max':
            data = maxs
        else:
            data = dict(agg)

        items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:50]
        if not items:
            return [], []
        return [i[0] for i in items], [i[1] for i in items]

    def _col_idx(self, cols, field_name, default=0):
        """Case-insensitive column lookup. Returns (index, found_flag)."""
        if not field_name:
            return default, False
        col_map = {c: i for i, c in enumerate(cols)}
        if field_name in col_map:
            return col_map[field_name], True
        ci = {c.lower(): i for i, c in enumerate(cols)}.get(field_name.lower())
        if ci is not None:
            return ci, True
        return default, False

    @staticmethod
    def _blend_hex(c1, c2, t):
        """Linearly interpolate between two hex colors by t (0.0–1.0)."""
        try:
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return c1

    @staticmethod
    def _fmt(v):
        if v is None:
            return ''
        try:
            f = float(str(v).replace(',', '.'))
            if f == int(f) and abs(f) < 1e15:
                return f'{int(f):,}'.replace(',', '.')
            return f'{f:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return str(v)

    def _css(self):
        return """<style>
.nf-dash{display:flex;flex-wrap:wrap;gap:14px;padding:6px;font-family:Arial,sans-serif;}
.nf-widget{background:#fff;border:1px solid #ddd;border-radius:8px;
  box-shadow:0 2px 8px rgba(0,0,0,0.09);overflow:hidden;box-sizing:border-box;}
.nf-whead{background:#2c3e50;color:#fff;padding:10px 16px;font-size:13px;
  font-weight:bold;letter-spacing:0.3px;}
.nf-wbody{padding:12px;overflow:auto;}
.nf-err{background:#fdf2f2;border:1px solid #e74c3c;color:#c0392b;
  padding:10px;border-radius:4px;font-size:12px;}
.nf-empty{color:#bbb;padding:24px;font-size:13px;text-align:center;}
.nf-note{color:#bbb;font-size:11px;margin-top:6px;text-align:right;}
</style>"""
