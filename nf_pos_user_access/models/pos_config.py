# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    allowed_user_ids = fields.Many2many(
        'res.users',
        'pos_config_user_rel',
        'pos_config_id',
        'user_id',
        string='Usuarios Permitidos',
        help='Usuarios que pueden acceder a este POS. Si está vacío, todos los usuarios con permisos de POS pueden acceder.'
    )
    
    user_access_restricted = fields.Boolean(
        string='Acceso Restringido',
        compute='_compute_user_access_restricted',
        store=True,
        help='Indica si este POS tiene acceso restringido a usuarios específicos'
    )
    
    current_user_has_access = fields.Boolean(
        string='Usuario Actual Tiene Acceso',
        compute='_compute_current_user_has_access',
        help='Indica si el usuario actual puede acceder a este POS'
    )
    
    @api.depends('allowed_user_ids')
    def _compute_user_access_restricted(self):
        """Calcula si el POS tiene restricción de acceso."""
        for config in self:
            config.user_access_restricted = bool(config.allowed_user_ids)
    
    @api.depends('allowed_user_ids')
    def _compute_current_user_has_access(self):
        """Calcula si el usuario actual tiene acceso a este POS."""
        for config in self:
            config.current_user_has_access = config._check_user_access()
    
    def _check_user_access(self, user_id=None):
        """
        Verifica si un usuario tiene acceso a esta configuración de POS.
        
        Args:
            user_id: ID del usuario a verificar. Si no se especifica, usa el usuario actual.
        
        Returns:
            bool: True si el usuario tiene acceso, False en caso contrario.
        """
        self.ensure_one()
        
        # Si no hay usuarios específicos asignados, todos tienen acceso
        if not self.allowed_user_ids:
            return True
        
        # Obtener el usuario a verificar
        if user_id is None:
            user_id = self.env.user.id
        
        # Verificar si el usuario está en la lista de permitidos
        return user_id in self.allowed_user_ids.ids
    
    def open_ui(self):
        """Override para verificar acceso antes de abrir el POS."""
        self.ensure_one()
        
        # Verificar acceso del usuario actual
        if not self._check_user_access():
            raise AccessError(_(
                'No tienes permiso para acceder a este Punto de Venta.\n'
                'Contacta con tu administrador si necesitas acceso.'
            ))
        
        return super(PosConfig, self).open_ui()
    
    def open_existing_session_cb(self):
        """Override para verificar acceso antes de abrir sesión existente."""
        self.ensure_one()
        
        if not self._check_user_access():
            raise AccessError(_(
                'No tienes permiso para acceder a este Punto de Venta.\n'
                'Contacta con tu administrador si necesitas acceso.'
            ))
        
        return super(PosConfig, self).open_existing_session_cb()
