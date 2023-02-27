# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from datetime import datetime
from odoo import _, api, fields, models
from odoo.addons.iap import jsonrpc
from odoo.exceptions import RedirectWarning
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)
# DEFAULT_ENDPOINT = "https://ewaybill.odoo.co.in"
DEFAULT_ENDPOINT = "https://ewaybill-sandbox.odoo.co.in"  # Sandbox Endpoint


class WaybillService(models.Model):
    _name = "l10n.in.ewaybill.service"
    _description = "eInvoice Client"

    partner_id = fields.Many2one("res.partner", string="GSTN Partner")
    gstin = fields.Char("GSTIN")
    gstn_username = fields.Char("Username")
    gstn_password = fields.Char("Password")

    @api.model
    def get_service(self, partner):
        """Get the active eWayBill service, if already configured.
        If not return the wizard to configure the eWayBill service."""

        service = self.search(
            [("partner_id", "=", partner.id), ("gstin", "=", partner.vat)], limit=1
        )
        if not service:
            action = self.env.ref(
                "l10n_in_ewaybill.l10n_in_ewaybill_generate_token_wizard_action"
            )
            raise RedirectWarning(
                "Please configure GSTN IAP Service for %s with GSTIN: %s"
                % (partner.name, partner.vat),
                action.id,
                _("Configure"),
            )
        return service

    def _connect_to_server(self, url, params):
        """Connect to Odoo IAP server to process all the request.
        The default production server is running at https://ewaybill.odoo.co.in"""

        def __get_error_codes(response_josn):
            code = safe_eval(response_josn.get("message", {})).get("errorCodes", False)
            codes = code.split(",")
            codes = list(map(int, codes))
            return codes

        self.ensure_one()
        iap_service = self.env["iap.account"].get("ewaybill_india")
        params.update(
            {
                "account_token": iap_service.account_token,
                "gst_username": self.gstn_username,
                "gst_number": self.gstin,
            }
        )
        endpoint = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ewaybill_india.endpoint", DEFAULT_ENDPOINT)
        )
        url = "%s%s" % (endpoint, url)
        _logger.info('Parameter for Eway Bill: %s', params)
        response = jsonrpc(url, params=params, timeout=3000)
        if response.get("error", False):
            codes = __get_error_codes(response.get("error"))
            if 238 in codes and self.gstn_password:
                """Check if password is saved,
                directly make the call to authenticate method
                """
                # TODO: need to check for the recursion
                return self.authenticate(self.gstn_password)

            if 238 in codes and not self.gstn_password:
                """Check if password is not saved,
                initialise the same wizard used for the setup.
                """
                action = self.env.ref(
                    "l10n_in_ewaybill.l10n_in_ewaybill_generate_token_wizard_action"
                )
                raise RedirectWarning(
                    "Please configure GSTN IAP Service for %s with GSTIN: %s"
                    % (self.partner_id.name, self.partner_id.vat),
                    action.id,
                    _("Configure"),
                )

        return response

    def authenticate(self, gstn_password=None):
        self.ensure_one()
        password = gstn_password or self.gstn_password
        params = {"password": password}
        self._connect_to_server(url="/iap/ewaybill/authenticate", params=params)

    def setup(self, gstn_password=None, source_document=None):
        """Setup the IAP service and account at https://ewaybill.odoo.co.in"""

        self.ensure_one()
        password = gstn_password or self.gstn_password
        params = {"password": password, "source_document": "Unknown"}
        self._connect_to_server(url="/iap/ewaybill/setup", params=params)

    def submit(self, transaction_id):
        """Submit the eWayBill JSON data to https://ewaybill.odoo.co.in.
        Receive the eWayBill data generated at https://ewaybill.nic.in."""
        self.ensure_one()
        params = {
            "password": self.gstn_password,
            "json_payload": json.loads(transaction_id.request_json),
            "source_document": transaction_id._get_source_document(),
        }
        response = self._connect_to_server(url="/iap/ewaybill/generate", params=params)
        return response

    def cancel(self, transaction_id):
        self.ensure_one()
        params = {
            "password": self.gstn_password,
            "json_payload": json.loads(transaction_id.request_json),
            "source_document": transaction_id._get_source_document(),
        }
        response = self._connect_to_server(url="/iap/ewaybill/cancel", params=params)
        return response

    def update_part_b(self, transaction_id):
        self.ensure_one()
        params = {
            "password": self.gstn_password,
            "json_payload": json.loads(transaction_id.request_json),
            "source_document": transaction_id._get_source_document(),
        }
        response = self._connect_to_server(
            url="/iap/ewaybill/update/partb", params=params
        )
        return response

    def update_part_b_transporter_id(self, transaction_id):
        self.ensure_one()
        params = {
            "password": self.gstn_password,
            "json_payload": json.loads(transaction_id.request_json),
            "source_document": transaction_id._get_source_document(),
        }
        response = self._connect_to_server(
            url="/iap/ewaybill/update/transporter", params=params
        )
        return response

    def extend(self, transaction_id):
        self.ensure_one()
        params = {
            "password": self.gstn_password,
            "json_payload": json.loads(transaction_id.request_json),
            "source_document": transaction_id._get_source_document(),
        }
        response = self._connect_to_server(url="/iap/ewaybill/extend", params=params)
        return response
