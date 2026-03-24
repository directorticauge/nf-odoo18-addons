# -*- coding: utf-8 -*-
{
    'name': 'NF POS User Access Control',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Controla qué usuarios pueden acceder a cada configuración de POS',
    'description': """
        Control de Acceso por Usuario a Configuraciones POS
        ====================================================
        
        Este módulo permite restringir el acceso a configuraciones específicas 
        de Punto de Venta (POS) por usuario.
        
        Funcionalidades:
        ----------------
        - Asignar usuarios permitidos a cada configuración de POS
        - Solo usuarios autorizados pueden abrir sesiones en ese POS
        - Filtrado automático: usuarios solo ven los POS a los que tienen acceso
        - Si no se asignan usuarios específicos, todos pueden acceder (comportamiento por defecto)
        
        Casos de uso:
        -------------
        - Asignar cajeros específicos a cajas específicas
        - Limitar vendedores a POS de su sucursal/tienda
        - Control de seguridad por configuración de POS
        - Separar accesos entre diferentes turnos o equipos
        
        Configuración:
        --------------
        En cada configuración de POS:
        1. Ve a la pestaña "Control de Acceso"
        2. Selecciona los usuarios que pueden usar este POS
        3. Si dejas vacío, todos los usuarios con permiso de POS pueden acceder
    """,
    'author': 'NF Soluciones',
    'website': 'https://www.augesoluciones.com',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/pos_config_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
