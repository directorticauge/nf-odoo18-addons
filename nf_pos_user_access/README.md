# POS User Access Control

## Descripción
Módulo para Odoo 18.0 que permite controlar qué usuarios pueden acceder a cada configuración de Punto de Venta (POS).

## Funcionalidades

### Control de Acceso por Usuario
- ✅ Asignar usuarios específicos a cada configuración de POS
- ✅ Solo usuarios autorizados pueden abrir sesiones
- ✅ Filtrado automático: cada usuario solo ve los POS a los que tiene acceso
- ✅ Si no se asignan usuarios, todos pueden acceder (comportamiento por defecto)

### Validaciones de Seguridad
- 🔒 Bloqueo al intentar abrir un POS sin autorización
- 🔒 Bloqueo al intentar crear una sesión sin permiso
- 🔒 Bloqueo al abrir la interfaz de un POS restringido
- 🔒 Filtrado automático en vistas de lista y kanban

### Indicadores Visuales
- 🎨 Etiqueta "Acceso Restringido" en formularios
- 🎨 Columna "Restringido" en vista de lista
- 🎨 Icono de candado en vista kanban
- 🎨 Contador de usuarios autorizados

## Casos de Uso

### 1. Cajeros por Caja
```
POS: Caja Principal
Usuarios permitidos: Juan Pérez, María García

→ Solo Juan y María pueden abrir sesiones en Caja Principal
```

### 2. Vendedores por Sucursal
```
POS: Tienda Centro
Usuarios permitidos: Vendedores del equipo Centro

POS: Tienda Norte
Usuarios permitidos: Vendedores del equipo Norte

→ Cada vendedor solo ve y accede a su tienda
```

### 3. Separación por Turnos
```
POS: Caja Turno Mañana
Usuarios permitidos: Equipo turno mañana

POS: Caja Turno Tarde
Usuarios permitidos: Equipo turno tarde
```

## Configuración

### Paso 1: Instalar el Módulo
1. Subir el ZIP a Odoo
2. Actualizar lista de aplicaciones
3. Instalar "POS User Access Control"

### Paso 2: Configurar Accesos
1. Ir a **Punto de Venta → Configuración → Punto de Venta**
2. Abrir la configuración de POS que quieres restringir
3. Ir a la pestaña **"Control de Acceso"**
4. Seleccionar los usuarios que pueden usar este POS
5. Guardar

### Paso 3: Resultado
- Los usuarios seleccionados verán el POS en su lista
- Los demás usuarios NO lo verán ni podrán acceder
- Si intentan acceder directamente, verán un error de permisos

## Comportamiento

### Sin Usuarios Asignados
- **Campo vacío** = Todos los usuarios con permisos de POS pueden acceder
- Comportamiento por defecto de Odoo

### Con Usuarios Asignados
- **Solo usuarios en la lista** pueden acceder
- Los demás no ven el POS en sus listas
- Mensaje de error si intentan acceder: *"No tienes permiso para acceder a este Punto de Venta"*

## Mensajes de Error

```
❌ No tienes permiso para acceder a este Punto de Venta.
   Contacta con tu administrador si necesitas acceso.
```

```
❌ No tienes permiso para abrir una sesión en el Punto de Venta "Caja Principal".
   Contacta con tu administrador si necesitas acceso.
```

## Compatibilidad
- Odoo 18.0
- Módulo base: `point_of_sale`
- Compatible con otros módulos de POS

## Notas Importantes

⚠️ **Los administradores también deben estar en la lista**
- Si restringes un POS, incluso los administradores deben estar en la lista de usuarios permitidos
- Los administradores pueden CONFIGURAR cualquier POS, pero para USARLO deben estar autorizados

⚠️ **Sesiones existentes**
- Las sesiones ya abiertas NO se cierran al activar restricciones
- Las restricciones aplican al abrir NUEVAS sesiones

## Autor
Auge Soluciones
