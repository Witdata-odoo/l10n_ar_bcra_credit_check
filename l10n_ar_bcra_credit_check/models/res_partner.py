import requests
from datetime import date
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    bcra_credit_status = fields.Char("Estado Crediticio BCRA", readonly=True)
    bcra_last_update = fields.Date("Última Actualización BCRA", readonly=True)
    bcra_credit_detail = fields.Text("Detalle del Estado Crediticio", readonly=True)
    bcra_rejected_checks = fields.Text("Cheques Rechazados", readonly=True)

    def consultar_estado_crediticio_bcra(self):
        for partner in self:
            # Validación del CUIT/CUIL
            if not partner.vat or len(partner.vat) != 11:
                _logger.warning("El cliente no tiene un CUIT/CUIL válido registrado.")
                partner.update({
                    "bcra_credit_status": "CUIT/CUIL inválido",
                    "bcra_credit_detail": "",
                    "bcra_rejected_checks": "",
                })
                return {"error": "El cliente no tiene un CUIT/CUIL válido registrado."}

            # Endpoints de la API del BCRA
            url_deuda = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/{partner.vat}"
            url_cheques = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/ChequesRechazados/{partner.vat}"

            try:
                # **Consulta de deuda actual**
                response_deuda = requests.get(url_deuda, timeout=10, verify=False)
                response_deuda.raise_for_status()
                data_deuda = response_deuda.json()
                _logger.info("Respuesta de deuda BCRA: %s", data_deuda)

                if data_deuda.get("status") == 200 and "results" in data_deuda:
                    periodos = data_deuda["results"].get("periodos", [])
                    detalles_entidades = []
                    
                    for periodo in periodos:
                        # Añade el período al detalle de la entidad
                        periodo_fecha = periodo.get("periodo", "Sin periodo")
                        entidades = periodo.get("entidades", [])
                        for entidad in entidades:
                            situacion = entidad.get("situacion", "Desconocido")
                            detalles_entidades.append(
                                f"Período: {periodo_fecha}, "
                                f"Entidad: {entidad.get('entidad', 'N/A')}, "
                                f"Situación: {situacion}, "
                                f"Monto: {entidad.get('monto', 'N/A')}, "
                                f"Días de atraso: {entidad.get('diasAtrasoPago', 'N/A')}"
                            )
                    
                    # Actualiza `bcra_credit_status` y `bcra_credit_detail` con todos los detalles de entidades
                    partner.update({
                        "bcra_credit_status": f"Situación: {situacion}",
                        "bcra_last_update": date.today(),
                        "bcra_credit_detail": "\n".join(detalles_entidades),
                    })

                    # **Consulta de cheques rechazados**
                    response_cheques = requests.get(url_cheques, timeout=10, verify=False)
                    if response_cheques.status_code == 404:
                        partner.bcra_rejected_checks = "Sin cheques rechazados"
                    else:
                        response_cheques.raise_for_status()
                        data_cheques = response_cheques.json()
                        _logger.info("Respuesta de cheques rechazados BCRA: %s", data_cheques)

                        if data_cheques.get("status") == 200 and "results" in data_cheques:
                            causales = data_cheques["results"].get("causales", [])
                            cheques_rechazados = []
                            
                            # Itera sobre todas las causales y entidades para capturar todos los detalles de cheques rechazados
                            for item in causales:
                                for entidad in item.get("entidades", []):
                                    for detalle in entidad.get("detalle", []):
                                        cheques_rechazados.append(
                                            f"{item['causal']} - Cheque N° {detalle['nroCheque']} "
                                            f"(${detalle['monto']}) - Entidad: {entidad.get('entidad', 'N/A')}"
                                        )

                            # Almacena todos los cheques rechazados en el campo `bcra_rejected_checks`
                            partner.bcra_rejected_checks = "\n".join(cheques_rechazados) if cheques_rechazados else "Sin cheques rechazados disponibles"
                        else:
                            partner.bcra_rejected_checks = "No disponible"
                else:
                    partner.update({
                        "bcra_credit_status": "Sin datos",
                        "bcra_credit_detail": "",
                        "bcra_rejected_checks": "",
                    })

            except requests.exceptions.Timeout:
                partner.update({
                    "bcra_credit_status": "Timeout al conectar",
                    "bcra_credit_detail": "",
                    "bcra_rejected_checks": "",
                })
            except requests.exceptions.RequestException as e:
                partner.update({
                    "bcra_credit_status": "Error de conexión",
                    "bcra_credit_detail": "",
                    "bcra_rejected_checks": "",
                })
