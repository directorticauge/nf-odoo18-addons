# 🚀 INSTALACIÓN RÁPIDA - md_pos_general_note

## ⚡ Instalación en 3 Pasos

### 1️⃣ Copiar el Módulo

```bash
# Si estás en el directorio actual:
cp -r md_pos_general_note /ruta/a/odoo/addons/

# O si usas Docker:
docker cp md_pos_general_note odoo_container:/mnt/extra-addons/
```

### 2️⃣ Actualizar Lista de Aplicaciones

En Odoo:
1. **Apps** (Aplicaciones)
2. Clic en los **3 puntos** (⋮) → **Update Apps List** (Actualizar lista de aplicaciones)
3. Buscar: `general note` o `nota general`
4. Clic en **Install** (Instalar)

### 3️⃣ Usar en el POS

1. Abrir sesión del POS
2. Agregar productos
3. Clic en botón **"Nota"** (icono 📝)
4. Escribir nota
5. Confirmar

✅ **Listo!** La nota aparecerá en el recibo sin generar líneas en la factura.

---

## 🔍 Verificación

### Verificar que NO genera línea en factura:

1. Crear una orden con nota en el POS
2. Ir a **Point of Sale** → **Orders** → Seleccionar la orden
3. Clic en **Invoice** (Factura)
4. Ver las líneas de la factura creada
5. ✅ Solo deben aparecer los productos, NO la nota
6. La nota está en el campo **Terms and Conditions** (Narration)

---

## 🆘 Solución de Problemas

### ❌ No aparece el botón "Nota"

**Solución:**
```bash
# Limpiar assets
# En Odoo: Settings → Developer Tools → Clear Assets Bundle
# O reiniciar Odoo:
sudo systemctl restart odoo

# Luego en el navegador:
Ctrl + Shift + R (Limpiar caché)
```

### ❌ Error al instalar

**Solución:**
```bash
# Ver logs de Odoo
tail -f /var/log/odoo/odoo.log

# Verificar que el módulo está en addons_path
grep addons_path /etc/odoo/odoo.conf

# Reiniciar con actualización de módulo
odoo -u md_pos_general_note -d nombre_base_datos
```

### ❌ La nota aparece como línea en factura

**Causa:** Estás usando un producto llamado "Nota" en lugar del botón.

**Solución:** Usa el **botón "Nota"** del POS, no agregues productos de nota.

---

## 📋 Dependencias

- **Odoo**: 18.0
- **Módulos requeridos**: `point_of_sale`
- **Módulos opcionales**: Ninguno

---

## 🎯 Características

✅ Campo `general_note` en `pos.order`  
✅ Botón intuitivo en interfaz POS  
✅ Popup para escribir notas  
✅ Nota visible en recibo impreso  
✅ NO genera líneas en `account.move`  
✅ Compatible con DIAN Colombia  
✅ Se guarda como `narration` en factura  

---

## 💡 Casos de Uso Típicos

```
Ejemplo 1 - Instrucciones de entrega:
"Entregar en Mesa 5
Sin cebolla - cliente alérgico"

Ejemplo 2 - Datos de facturación:
"Factura a nombre de: EMPRESA ABC S.A.S
NIT: 900123456-7
Email: facturacion@empresa.com"

Ejemplo 3 - Observaciones de cocina:
"Papas bien doradas
Carne término medio
Extra salsa de ajo"

Ejemplo 4 - Referencias de pago:
"Pago con transferencia
Referencia: TRF-2026-001234"
```

---

## 🔄 Actualización

```bash
# Actualizar el módulo
odoo -u md_pos_general_note -d nombre_base_datos

# O desde la interfaz:
# Apps → POS General Note → Upgrade
```

---

## 📞 Soporte

**Desarrollador:** MaraDev  
**Versión:** 18.0.1.0  
**Licencia:** OPL-1  

---

## ✅ Checklist Post-Instalación

- [ ] Módulo instalado en Apps
- [ ] Botón "Nota" visible en POS
- [ ] Popup abre al hacer clic
- [ ] Nota aparece en recibo
- [ ] Nota NO genera línea en factura
- [ ] Factura DIAN valida correctamente

**¡Todo listo para usar!** 🎉
