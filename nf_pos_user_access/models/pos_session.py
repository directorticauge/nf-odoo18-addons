# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import AccessError


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para validar que el usuario tenga acceso
        al POS antes de crear una sesión.
        """
        for vals in vals_list:
            config_id = vals.get('config_id')
            if config_id:
                config = self.env['pos.config'].browse(config_id)
                if not config._check_user_access():
                    raise AccessError(_(
                        'No tienes permiso para abrir una sesión en el Punto de Venta "%s".\n'
                        'Contacta con tu administrador si necesitas acceso.'
                    ) % config.name)
        
        return super(PosSession, self).create(vals_list)
    
    def open_frontend_cb(self):
        """
        Override para verificar acceso antes de abrir la interfaz del POS.
        """
        self.ensure_one()
        
        if not self.config_id._check_user_access():
            raise AccessError(_(
                'No tienes permiso para acceder a este Punto de Venta.\n'
                'Contacta con tu administrador si necesitas acceso.'
            ))
        
        return super(PosSession, self).open_frontend_cb()
