# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'
    invoice_name = fields.Char('# Invoice', related='account_move.name')
    invoice_cufe = fields.Char('CUFE', related='account_move.cufe')
    invoice_qr = fields.Char('QR Code', compute='_compute_invoice_qr')

    @api.depends('account_move', 'account_move.qr_code')
    def _compute_invoice_qr(self):
        for order in self:
            if order.account_move and order.account_move.qr_code:
                qr_code = order.account_move.qr_code
                if isinstance(qr_code, bytes):
                    order.invoice_qr = qr_code.decode('utf-8')
                else:
                    order.invoice_qr = qr_code
            else:
                order.invoice_qr = ''

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        res.update({
            'invoice_name': order.invoice_name,
            'invoice_cufe': order.invoice_cufe,
            'invoice_qr': order.invoice_qr,
        })
        return res

    # def _export_for_ui(self, order):
    #     res = super(PosOrder, self)._export_for_ui(order)
    #     res.update({'invoice_name': order.account_move.name if order.account_move else False})
    #     return res

    def get_pos_invoice_name(self):
        for order in self:
            return order.account_move.name if order.account_move else False
