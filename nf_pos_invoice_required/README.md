# POS - Factura Obligatoria

## Descripción

Este módulo hace que la opción "Recibo/Factura" en el Punto de Venta siempre esté marcada y sea obligatoria.

## Características

- ✅ **Todas las órdenes generarán factura OBLIGATORIAMENTE** (forzado en backend)
- ✅ Se puede activar/desactivar por cada POS mediante campo "Factura Obligatoria"
- ✅ Validación confiable en Python - sin errores
- ⚠️ **Nota:** El checkbox visualmente se puede desmarcar, PERO al guardar la orden Python FUERZA `to_invoice = True`
- ✅ Funcionamiento garantizado - la factura SIEMPRE se generará

## Configuración

1. Ve a **Punto de Venta > Configuración > Puntos de Venta**
2. Abre la configuración del POS que deseas
3. En la sección de facturas, marca **"Factura Obligatoria"**
4. Guarda los cambios

## Funcionamiento

Una vez activado:
- Cada nueva orden en el POS tendrá `to_invoice = True` automáticamente
- El usuario no podrá desmarcar el checkbox "Recibo/Factura"
- Todas las ventas generarán su correspondiente factura

## Instalación

1. Copia el módulo a tu carpeta de addons
2. Actualiza la lista de aplicaciones
3. Instala "POS - Factura Obligatoria"

## Dependencias

- point_of_sale

## Versión

- Odoo 18.0
- Versión del módulo: 1.0.0

## Autor

Tu Empresa
