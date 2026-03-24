/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

console.log('🔧 MD Network Printer Extension Loading...');

// Global configuration
window.NETWORK_PRINTER_URL = 'https://192.168.1.77:5001/print';
window._lastOrderData = null;

// Patch PosStore to capture order data before printing
patch(PosStore.prototype, {
    async sendOrderInPreparationUpdateLastChange(order, cancelled = false) {
        console.log('📦 Capturing order for kitchen printing:', order);
        
        // Store order data globally so fetch interceptor can access it
        if (order) {
            // Get table name - try multiple properties
            let tableName = 'N/A';
            if (order.table_id) {
                tableName = order.table_id.display_name || 
                           order.table_id.name || 
                           (order.table_id.table_number ? 'Mesa ' + order.table_id.table_number : null) ||
                           (order.table_id.identifier ? order.table_id.identifier : null) ||
                           'Mesa';
                console.log('📍 Table object:', order.table_id);
            }
            
            window._lastOrderData = {
                name: order.name || order.pos_reference || order.tracking_number || 'Sin número',
                table: tableName,
                lines: [],
                timestamp: new Date()
            };
            
            // Get order lines - lines is an array of PosOrderline objects
            const lines = order.lines || [];
            lines.forEach(line => {
                const product = line.product_id || line.full_product_name;
                let productName = 'Producto';
                
                if (typeof product === 'string') {
                    productName = product;
                } else if (product && product.display_name) {
                    productName = product.display_name;
                } else if (product && product.name) {
                    productName = product.name;
                } else if (line.full_product_name) {
                    productName = line.full_product_name;
                }
                
                const qty = line.qty || line.quantity || 1;
                const note = line.note || line.customer_note || '';
                
                window._lastOrderData.lines.push({
                    name: productName,
                    qty: qty,
                    note: note
                });
            });
            
            console.log('✅ Captured order data:', window._lastOrderData);
        }
        
        return super.sendOrderInPreparationUpdateLastChange(...arguments);
    }
});

// Store original fetch
const originalFetch = window.fetch;

// Override global fetch to intercept Epson printer requests
window.fetch = async function(...args) {
    const [url, options] = args;
    const urlString = typeof url === 'string' ? url : url.toString();
    
    // Check if this is an Epson printer request
    if (urlString.includes('/cgi-bin/epos/service.cgi')) {
        console.log('🖨️ Intercepted Epson printer request');
        
        const networkPrinterUrl = window.NETWORK_PRINTER_URL;
        
        if (networkPrinterUrl) {
            console.log('✅ Redirecting to network printer:', networkPrinterUrl);
            
            try {
                // Generate ticket from captured order data
                let ticket = "\x1b@"; // ESC @ Initialize
                ticket += "\x1b\x61\x01"; // Center align
                ticket += "================================\n";
                ticket += "  COMANDA DE COCINA  \n";
                ticket += "================================\n";
                ticket += "\x1b\x61\x00"; // Left align
                
                if (window._lastOrderData) {
                    const order = window._lastOrderData;
                    ticket += "Orden: " + order.name + "\n";
                    ticket += "Mesa: " + order.table + "\n";
                    ticket += "Fecha: " + order.timestamp.toLocaleString('es-CO', {
                        dateStyle: 'short',
                        timeStyle: 'short'
                    }) + "\n";
                    ticket += "--------------------------------\n\n";
                    
                    if (order.lines && order.lines.length > 0) {
                        order.lines.forEach(line => {
                            ticket += line.qty + "x " + line.name + "\n";
                            if (line.note) {
                                ticket += "   Nota: " + line.note + "\n";
                            }
                        });
                    } else {
                        ticket += "(Sin productos)\n";
                    }
                } else {
                    ticket += "Fecha: " + new Date().toLocaleString('es-CO', {
                        dateStyle: 'short',
                        timeStyle: 'short'
                    }) + "\n";
                    ticket += "--------------------------------\n\n";
                    ticket += "(Datos de orden no disponibles)\n";
                }
                
                ticket += "\n--------------------------------\n";
                ticket += "Enviado desde POS\n";
                ticket += "\n\n\n";
                ticket += "\x1dV\x41\x03"; // Cut paper
                
                console.log('📤 Sending ticket to network printer (size: ' + ticket.length + ' bytes)');
                console.log('📄 Ticket content:', ticket);
                
                // Send to network printer
                const response = await originalFetch(networkPrinterUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'text/plain; charset=utf-8',
                    },
                    body: ticket,
                });
                
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                
                console.log('✅ Successfully sent to network printer!');
                
                // Clear captured data
                window._lastOrderData = null;
                
                // Return a fake successful Epson response
                return new Response(
                    '<?xml version="1.0" encoding="utf-8"?><response success="true" code="OK" status="0"/>',
                    {
                        status: 200,
                        statusText: 'OK',
                        headers: { 
                            'Content-Type': 'text/xml',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
                );
                
            } catch (err) {
                console.error('❌ Network printer error:', err);
                
                return new Response(
                    '<?xml version="1.0" encoding="utf-8"?><response success="false" code="ERROR"/>',
                    {
                        status: 500,
                        statusText: 'Network Printer Error: ' + err.message,
                        headers: { 'Content-Type': 'text/xml' }
                    }
                );
            }
        }
    }
    
    // Default: call original fetch
    return originalFetch.apply(this, args);
};

console.log('✅ MD Network Printer Extension Loaded');
console.log('📡 Network printer URL:', window.NETWORK_PRINTER_URL);
