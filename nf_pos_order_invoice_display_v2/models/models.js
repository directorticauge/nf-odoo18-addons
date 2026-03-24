/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(vals);
        this.invoice_name = vals.invoice_name || ''
        this.invoice_cufe = vals.invoice_cufe || ''
    },
    export_for_printing() {
        const export_for_printing = super.export_for_printing(...arguments);
        export_for_printing.headerData.invoice_name = this.invoice_name || '';
        export_for_printing.headerData.invoice_cufe = this.invoice_cufe || '';
        return export_for_printing
    },
    get_invoice_name() { return this.invoice_name ? this.invoice_name : ''; },
    get_invoice_cufe() { return this.invoice_cufe ? this.invoice_cufe : ''; },
})