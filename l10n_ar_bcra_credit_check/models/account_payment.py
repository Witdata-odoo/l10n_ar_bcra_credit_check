from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = "account.payment"

    bcra_credit_status_info = fields.Char(
        string="Situación Crediticia BCRA",
        related="partner_id.bcra_credit_status",
        help="""Categorías de Situación Crediticia del BCRA:
Situación 1 - Normal: Pagas en tiempo y forma, sin atrasos en los pagos. 
Situación 2 - Riesgo Bajo: Atrasos en el pago de entre 30 y 90 días, o pago del monto mínimo de una deuda. 
Situación 3 - Riesgo Medio: Atrasos en el pago de entre 90 y 180 días. 
Situación 4 - Riesgo Alto: Atrasos en el pago de entre 180 y 365 días. 
Situación 5 - Irrecuperable: Deudas impagas con más de 365 días de atraso. """,
        store=False,
        readonly=True,
    )

    bcra_rejected_checks_status = fields.Char(
    string="¿Tiene Cheques Rechazados?",
    related="partner_id.bcra_rejected_checks_status",
    store=False,
    readonly=True,
    )
