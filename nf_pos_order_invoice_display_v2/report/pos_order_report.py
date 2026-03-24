# -*- coding: utf-8 -*-
from odoo import fields, models


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"
    account_move = fields.Many2one(comodel_name='account.move', string='# Invoice', readonly=True)

    def _select(self):
        return super(PosOrderReport, self)._select() + """, s.account_move as account_move"""

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ", s.account_move"
