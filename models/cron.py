from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"
    


    def ejecutar_cron_estado_crediticio_bcra(self):
        offset = 0
        limit = 100  # Ajustar según capacidad del servidor
        while True:
            partners = self.search([('vat', '!=', False)], offset=offset, limit=limit)
            if not partners:
                break
            for partner in partners:
                try:
                    partner.consultar_estado_crediticio_bcra()
                except Exception as e:
                    _logger.error("Error procesando BCRA para partner %s: %s", partner.name, str(e))
            self.env.cr.commit()  # Importante para evitar rollback en batch grande
            offset += limit