# NF Support CMD — Gestión de Comodatos

Módulo para administración de equipos en comodato (neveras, dispensadores, cuartos fríos, termoneveras).

## Estructura

```
nf_support_cmd/
├── models/
│   ├── cmd_equipment.py     ← Inventario maestro de equipos
│   ├── cmd_assignment.py    ← Asignaciones a clientes
│   └── cmd_service.py       ← Salidas de servicio / mantenimiento
├── views/
│   ├── cmd_equipment_views.xml
│   ├── cmd_assignment_views.xml
│   ├── cmd_service_views.xml
│   └── menu.xml
└── security/
    └── ir.model.access.csv
```

## Modelos

### nf.cmd.equipment
Inventario de cada equipo físico. Estados:
- **Disponible en Patio** → en bodega interna
- **Asignado a Cliente** → con contrato activo
- **En Mantenimiento** → fuera de servicio temporal
- **Por Localizar** → equipo no ubicado
- **Dado de Baja** → retirado del inventario

### nf.cmd.assignment
Registro de cada asignación (cliente, fechas, ruta, ciudad). Al crear una asignación activa el equipo pasa automáticamente al estado "Asignado". Al devolver, vuelve a "Disponible".

### nf.cmd.service
Log de salidas de servicio: mantenimientos, reparaciones, entregas, recogidas.
