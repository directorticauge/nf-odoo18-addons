/** @odoo-module */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    getInvoiceName(order) { return order.get_invoice_name(); },
    _getSearchFields() {
        const fields = super._getSearchFields();
        fields.MY_CUSTOM_FIELD = {
            repr: (order) => order.get_invoice_name(),
            displayName: "# Invoice",
            modelField: "invoice_name",
        };
        return fields
    }
})