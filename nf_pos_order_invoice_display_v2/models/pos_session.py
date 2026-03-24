# -*- coding: utf-8 -*-
from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_order(self):
        params = super()._loader_params_pos_order()
        fields = params.get("search_params", {}).setdefault("fields", [])
        for field in ("invoice_name", "invoice_cufe", "invoice_qr"):
            if field not in fields:
                fields.append(field)
        return params
