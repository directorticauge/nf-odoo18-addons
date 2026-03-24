from odoo import api, fields, models


class MdDeliverySlipPrintWizard(models.TransientModel):
    _name = "md.delivery.slip.print.wizard"
    _description = "Delivery Slip Print Wizard"

    picking_id = fields.Many2one("stock.picking", required=True, readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "stock.picking" and self.env.context.get(
            "active_id"
        ):
            res.setdefault("picking_id", self.env.context["active_id"])
        return res

    def action_print(self):
        """Always print the receipt format (tirilla)"""
        self.ensure_one()
        return self.env.ref(
            "nf_delivery_slip_no_prices.action_report_delivery_slip_receipt"
        ).report_action(self.picking_id)
