/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

// Patch para sincronizar SOLO las notas que NO generen líneas
// NO sincronizamos note/customer_note porque otros módulos las convierten en productos
patch(PosStore.prototype, {
    async _save_to_server(orders, options) {
        // NO agregar general_note automáticamente porque otros módulos 
        // están creando líneas de producto desde el campo "note"
        // El usuario debe usar el campo general_note directamente desde backend
        return await super._save_to_server(...arguments);
    }
});
