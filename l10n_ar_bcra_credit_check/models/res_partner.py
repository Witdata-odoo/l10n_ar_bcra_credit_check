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
    bcra_rejected_checks_status = fields.Char(
        string="Cheques Rechazados",
        compute="_compute_bcra_rejected_checks_status",
        store=False,
    )

    # Etiqueta legible para cada código de situación crediticia BCRA
    _BCRA_SITUACION_LABELS = {
        1: "Normal",
        2: "Riesgo bajo",
        3: "Con problemas",
        4: "Alto riesgo de insolvencia",
        5: "Irrecuperable",
        6: "Irrecuperable por disposición técnica",
    }

    def consultar_estado_crediticio_bcra(self):
        for partner in self:
            if not partner.country_id or partner.country_id.code != "AR":
                _logger.info(
                    "Salteando consulta BCRA para %s: país distinto de AR",
                    partner.name,
                )
                partner.update({
                    "bcra_credit_status": "Disponible solo para clientes de Argentina",
                    "bcra_credit_detail": "",
                    "bcra_rejected_checks": "",
                })
                continue
            # Validación del CUIT/CUIL
            if not partner.vat or len(partner.vat) != 11:
                _logger.warning("El cliente no tiene un CUIT/CUIL válido registrado.")
                partner.update({
                    "bcra_credit_status": "CUIT/CUIL inválido",
                    "bcra_credit_detail": "",
                    "bcra_rejected_checks": "",
                })
                continue

            # Endpoints de la API del BCRA
            url_deuda = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/{partner.vat}"
            url_cheques = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/ChequesRechazados/{partner.vat}"

            # === 1) Consulta de DEUDAS (independiente) ===
            credit_status = None
            credit_detail = ""
            try:
                response_deuda = requests.get(url_deuda, timeout=15, verify=False)
                if response_deuda.status_code == 404:
                    credit_status = "Sin datos en BCRA"
                    credit_detail = "El BCRA no reporta deudas registradas para esta identificación."
                else:
                    response_deuda.raise_for_status()
                    data_deuda = response_deuda.json()
                    _logger.info("Respuesta de deuda BCRA: %s", data_deuda)

                    if data_deuda.get("status") == 200 and "results" in data_deuda:
                        results = data_deuda["results"]
                        denominacion = results.get("denominacion", "")
                        periodos = results.get("periodos", [])
                        detalles_entidades = []
                        situacion_max = 0  # peor caso entre todas las entidades/periodos
                        total_deuda = 0.0

                        for periodo in periodos:
                            periodo_fecha = periodo.get("periodo", "Sin periodo")
                            for entidad in periodo.get("entidades", []):
                                sit = entidad.get("situacion", 0)
                                try:
                                    sit_int = int(sit)
                                except (ValueError, TypeError):
                                    sit_int = 0
                                if sit_int > situacion_max:
                                    situacion_max = sit_int
                                monto = entidad.get("monto", 0) or 0
                                try:
                                    total_deuda += float(monto)
                                except (ValueError, TypeError):
                                    pass
                                detalles_entidades.append(
                                    f"Período: {periodo_fecha}, "
                                    f"Entidad: {entidad.get('entidad', 'N/A')}, "
                                    f"Situación: {sit_int} ({self._BCRA_SITUACION_LABELS.get(sit_int, 'Desconocida')}), "
                                    f"Monto: ${monto:,.2f}, "
                                    f"Días de atraso: {entidad.get('diasAtrasoPago', 'N/A')}"
                                )

                        if detalles_entidades:
                            label = self._BCRA_SITUACION_LABELS.get(situacion_max, "Desconocida")
                            header = (
                                f"{denominacion}\n" if denominacion else ""
                            ) + f"Peor situación reportada: {situacion_max} ({label}) · Total deuda: ${total_deuda:,.2f}\n"
                            credit_status = f"Situación {situacion_max} - {label}"
                            credit_detail = header + "\n".join(detalles_entidades)
                        else:
                            credit_status = "Sin deudas registradas"
                            credit_detail = denominacion or ""
                    else:
                        credit_status = "Respuesta inválida del BCRA"
                        credit_detail = ""
            except requests.exceptions.Timeout:
                credit_status = "Timeout al conectar (Deudas)"
                _logger.warning("Timeout consultando deudas BCRA para %s", partner.vat)
            except requests.exceptions.RequestException as e:
                credit_status = "Error de conexión (Deudas)"
                _logger.warning("Error consultando deudas BCRA para %s: %s", partner.vat, e)
            except Exception as e:
                credit_status = "Error inesperado (Deudas)"
                _logger.exception("Error inesperado consultando deudas BCRA")

            # === 2) Consulta de CHEQUES RECHAZADOS (independiente) ===
            rejected_checks = ""
            try:
                response_cheques = requests.get(url_cheques, timeout=15, verify=False)
                if response_cheques.status_code == 404:
                    rejected_checks = "Sin cheques rechazados"
                else:
                    response_cheques.raise_for_status()
                    data_cheques = response_cheques.json()
                    _logger.info("Respuesta de cheques rechazados BCRA: %s", data_cheques)

                    if data_cheques.get("status") == 200 and "results" in data_cheques:
                        causales = data_cheques["results"].get("causales", [])
                        cheques_list = []
                        for item in causales:
                            for entidad in item.get("entidades", []):
                                for detalle in entidad.get("detalle", []):
                                    cheques_list.append(
                                        f"{item.get('causal', 'N/A')} - "
                                        f"Cheque N° {detalle.get('nroCheque', 'N/A')} "
                                        f"(${detalle.get('monto', 0)}) - "
                                        f"Entidad: {entidad.get('entidad', 'N/A')}"
                                    )
                        rejected_checks = "\n".join(cheques_list) if cheques_list else "Sin cheques rechazados"
                    else:
                        rejected_checks = "Sin cheques rechazados"
            except requests.exceptions.Timeout:
                rejected_checks = "Timeout consultando cheques rechazados"
                _logger.warning("Timeout consultando cheques BCRA para %s", partner.vat)
            except requests.exceptions.RequestException as e:
                rejected_checks = "Error consultando cheques rechazados"
                _logger.warning("Error consultando cheques BCRA para %s: %s", partner.vat, e)
            except Exception as e:
                rejected_checks = "Error inesperado consultando cheques"
                _logger.exception("Error inesperado consultando cheques BCRA")

            # === 3) Persistir resultado conjunto ===
            partner.update({
                "bcra_credit_status": credit_status or "Sin datos",
                "bcra_credit_detail": credit_detail,
                "bcra_rejected_checks": rejected_checks,
                "bcra_last_update": date.today(),
            })

    @api.depends("bcra_rejected_checks")
    def _compute_bcra_rejected_checks_status(self):
        for partner in self:
            value = partner.bcra_rejected_checks or ""
            if value and "Sin cheques rechazados" not in value and "Error" not in value and "Timeout" not in value:
                partner.bcra_rejected_checks_status = "Sí"
            else:
                partner.bcra_rejected_checks_status = "No"
