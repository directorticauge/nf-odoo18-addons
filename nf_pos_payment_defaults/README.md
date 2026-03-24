# POS Payment Defaults

## Descripción
Módulo para Odoo 18.0 que asigna automáticamente medios de pago y fechas de vencimiento a facturas y notas de crédito generadas desde el Punto de Venta (POS).

## Funcionalidades

### Facturas de Venta (out_invoice)
- **Fecha de vencimiento**: Se asigna automáticamente 30 días después de la fecha de factura
- **Medio de pago**:
  - Si tiene saldo pendiente > $0.01: Se asigna **Crédito** (payment_mean_id=2)
  - Si está totalmente pagada: Se asigna **Efectivo** (payment_mean_id=10)

### Notas de Crédito (out_refund)
- **Medio de pago DIAN**: Si no tiene asignado ninguno, se asigna **Efectivo** por defecto
- **Medio de pago**:
  - Si tiene saldo pendiente > $0.01: Se asigna **Crédito** (payment_mean_id=2)
  - Si está totalmente conciliada: Se asigna **Efectivo** (payment_mean_id=10)

## Ventajas sobre Acciones Automatizadas
1. **Mejor rendimiento**: El código Python es más rápido que las acciones del servidor
2. **Sin conflictos**: No interfiere con otros módulos que extiendan account.move
3. **Más mantenible**: El código está en un módulo específico y versionado
4. **Evita errores**: Usa SQL directo para evitar recursión infinita

## Instalación
1. Copiar la carpeta `md_pos_payment_defaults` en tu carpeta de addons
2. Actualizar la lista de aplicaciones
3. Instalar el módulo "POS Payment Defaults"
4. **Desactivar** las acciones automatizadas equivalentes:
   - PAGO POS POR DEFECTO
   - PAGO POS POR DEFECTO notas

## Compatibilidad
- Odoo 18.0
- Requiere módulos: `point_of_sale`, `account`
- Compatible con localización colombiana (DIAN)

## Configuración de IDs
El módulo usa estos IDs para los medios de pago:
- `payment_mean_id = 2`: Crédito
- `payment_mean_id = 10`: Efectivo

Si en tu instalación estos IDs son diferentes, debes modificar el archivo `models/account_move.py` líneas donde aparecen estos valores.

## Autor
Auge Soluciones
