from odoo import models, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def ejecutar_cron_estado_crediticio_bcra(self):
        partners = self.search([('vat', '!=', False)])
        for partner in partners:
            try:
                partner.consultar_estado_crediticio_bcra()
            except Exception as e:
                _logger.error("Error procesando BCRA para partner %s: %s", partner.name, str(e))
