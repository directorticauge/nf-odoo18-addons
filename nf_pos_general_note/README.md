# POS General Note (No Invoice Line) - Compatible con DIAN

## 📋 Descripción

Módulo para Odoo 18 Point of Sale que permite agregar **notas generales** a las órdenes sin que estas generen líneas adicionales en la factura contable.

### ❌ Problema que Resuelve

Cuando se agregan notas o comentarios en el POS que crean productos/líneas adicionales, estas aparecen en la factura contable (`account.move`), causando:
- ❌ Rechazos por parte de DIAN (facturación electrónica Colombia)
- ❌ Líneas de factura que no corresponden a productos reales
- ❌ Problemas de validación en sistemas de facturación electrónica

### ✅ Solución

Este módulo agrega un campo de **nota general** que:
- ✅ Aparece en el recibo impreso del POS
- ✅ Se guarda en la orden (`pos.order`)
- ✅ NO genera líneas en la factura contable
- ✅ Se incluye como comentario interno (narration) en `account.move`
- ✅ Compatible con DIAN y facturación electrónica

---

## 🚀 Instalación

### 1. Copiar el Módulo

Copiar la carpeta `md_pos_general_note` a tu directorio de addons de Odoo:

```bash
cp -r md_pos_general_note /ruta/a/odoo/addons/
```

### 2. Actualizar Lista de Aplicaciones

En Odoo:
1. Ir a **Aplicaciones**
2. Clic en **Actualizar lista de aplicaciones**
3. Buscar: `POS General Note`
4. Clic en **Instalar**

### 3. Reiniciar Servicio (si es necesario)

```bash
sudo systemctl restart odoo
```

---

## 📖 Uso

### En el POS

1. **Abrir una sesión** del Punto de Venta
2. **Agregar productos** a la orden como siempre
3. **Clic en el botón "Nota"** (icono de sticky note) en la parte superior
4. **Escribir la nota general** en el popup que aparece
5. **Confirmar** para guardar la nota

La nota aparecerá:
- ✅ En el recibo impreso (sección "NOTA" con bordes punteados)
- ✅ En el formulario de la orden POS (campo "Nota General")
- ✅ Como comentario interno en la factura (campo `narration`)

### Indicador Visual

El botón "Nota" muestra:
- `Nota` - Sin nota agregada
- `✓ Nota` - Nota agregada (checkmark verde)

---

## 🔧 Características Técnicas

### Backend (Python)

**Archivo:** `models/pos_order.py`

- Campo `general_note` en modelo `pos.order`
- Override de `_prepare_invoice_vals()` para agregar nota como `narration` (comentario interno)
- Override de `_order_fields()` para sincronizar datos desde frontend
- Loader params para cargar campo en POS

### Frontend (JavaScript/OWL)

**Archivos:**
- `static/src/app/store/models.js` - Extiende modelo Order con campo `general_note`
- `static/src/app/nota_button/nota_button.js` - Componente botón con popup TextArea
- `static/src/app/nota_button/nota_button.xml` - Template del botón
- `static/src/app/receipt/receipt.xml` - Template para mostrar nota en recibo

### Vistas XML

**Archivo:** `views/pos_order_views.xml`

- Campo en formulario de `pos.order`
- Campo opcional en vista de árbol

---

## 🔍 Verificación

### 1. Verificar que NO genera línea en factura

```python
# En consola de Odoo (Debug):
order = env['pos.order'].search([('general_note', '!=', False)], limit=1)
print("Nota:", order.general_note)

# Crear factura
order.action_pos_order_invoice()

# Verificar líneas de factura
invoice = order.account_move
print("Líneas:", len(invoice.invoice_line_ids))
# Solo debe haber líneas de productos, NO de la nota

# Verificar que la nota está en narration
print("Narration:", invoice.narration)
# Debe aparecer: "Nota del POS: <tu nota>"
```

### 2. Verificar en DIAN

Al generar la factura electrónica XML:
- ✅ Solo aparecen líneas de productos reales
- ✅ La nota NO está en `<cac:InvoiceLine>`
- ✅ La validación DIAN debe pasar sin errores

---

## 🎯 Casos de Uso

### Ejemplo 1: Instrucciones de Entrega

```
Productos:
- Pizza Napolitana x1
- Coca-Cola x2

Nota General:
"Entregar en mesa 5, sin cebolla, cliente alérgico"
```

**Resultado:**
- Recibo imprime la nota
- Factura tiene 2 líneas (pizza y coca-cola)
- DIAN valida correctamente

### Ejemplo 2: Observaciones del Cliente

```
Productos:
- Hamburguesa Especial x2

Nota General:
"Cliente solicita papas bien doradas
Factura a nombre de: EMPRESA XYZ
NIT: 123456789-1"
```

**Resultado:**
- Nota visible en recibo
- No afecta la factura contable
- Información disponible para el negocio

---

## ⚙️ Configuración Avanzada

### Personalizar Apariencia del Recibo

Editar `static/src/app/receipt/receipt.xml`:

```xml
<div class="pos-receipt-general-note" style="
    margin-top: 12px; 
    margin-bottom: 12px; 
    border-top: 2px solid #000;  <!-- Borde sólido -->
    background-color: #f0f0f0;   <!-- Fondo gris -->
    padding: 10px;
">
```

### Cambiar Posición del Botón

Editar `static/src/app/nota_button/nota_button.js`:

```javascript
ProductScreen.addControlButton({
    component: GeneralNoteButton,
    position: ['before', 'OrderlineCustomerNoteButton'], // Cambiar posición
});
```

---

## 🐛 Solución de Problemas

### Problema: No aparece el botón "Nota"

**Solución:**
1. Limpiar caché del navegador (Ctrl+Shift+R)
2. Cerrar y reabrir la sesión del POS
3. Verificar que el módulo está instalado correctamente

### Problema: La nota aparece en la factura como línea

**Solución:**
1. Verificar que NO estás usando un producto llamado "Nota"
2. Este módulo usa un CAMPO, no un producto
3. Revisar que `_prepare_invoice_vals()` se ejecutó correctamente

### Problema: Error en DIAN

**Causa:** Probablemente hay otro módulo creando líneas adicionales

**Solución:**
1. Revisar otros módulos que modifiquen la factura
2. Verificar el XML de factura electrónica generado
3. Asegurar que solo hay líneas de productos reales

---

## 📞 Soporte

- **Desarrollador:** MaraDev
- **Versión Odoo:** 18.0
- **Licencia:** OPL-1

---

## 📝 Changelog

### Version 18.0.1.0
- ✨ Versión inicial
- ✅ Campo general_note en pos.order
- ✅ Botón en POS con popup TextArea
- ✅ Nota en recibo impreso
- ✅ Compatible con DIAN (no genera líneas en factura)
- ✅ Integración con account.move (narration)
