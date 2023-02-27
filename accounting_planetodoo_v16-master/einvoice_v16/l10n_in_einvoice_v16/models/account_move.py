# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import logging
from odoo import fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_in_transaction_id = fields.Many2one(
        "l10n.in.einvoice.transaction", "GSTN Transaction", copy=False
    )
    l10n_in_transaction_status = fields.Selection(
        related="l10n_in_transaction_id.status", string="GSTN Transaction Status"
    )

    def _extract_digits(self, string):
        matches = re.findall(r"\d+", string)
        result = "".join(matches)
        return result

    def _validate_invoice_data(self):
        self.ensure_one()

        message = str()
        if not self.name or not re.match("^.{1,16}$", self.name):
            message += "\n- Invoice number should not be more than 16 charactor"
        for line in self.invoice_line_ids:
            if line.product_id and (
                not line.product_id.l10n_in_hsn_code
                or not re.match("^[0-9]+$", line.product_id.l10n_in_hsn_code)
            ):
                message += "\n- HSN code required for product %s" % (
                    line.product_id.name
                )

        if message:
            raise UserError(
                "Data not valid for the Invoice: %s\n%s" % (self.name, message)
            )

    def _validate_legal_identity_data(self, partner, is_company=False):
        self.ensure_one()

        message = str()
        if not partner:
            raise UserError("Error: Customer not found!")
        if is_company and partner.country_id.code != "IN":
            message += "\n- Country should be India"
        if not re.match("^.{3,100}$", partner.street or ""):
            message += "\n- Street required min 3 and max 100 charactor"
        if partner.street2 and not re.match("^.{3,100}$", partner.street2):
            message += "\n- Street2 should be min 3 and max 100 charactor"
        if not re.match("^.{3,100}$", partner.city or ""):
            message += "\n- City required min 3 and max 100 charactor"
        if not re.match("^.{3,50}$", partner.state_id.name or ""):
            message += "\n- State required min 3 and max 50 charactor"
        if partner.country_id.code == "IN" and not re.match(
            "^[0-9]{6,}$", partner.zip or ""
        ):
            message += "\n- Zip code required 6 digites"
        if partner.phone and not re.match(
            "^[0-9]{10,12}$", self._extract_digits(partner.phone)
        ):
            message += "\n- Mobile number should be minimum 10 or maximum 12 digites"
        if partner.email and (
            not re.match(
                r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$", partner.email
            )
            or not re.match("^.{3,100}$", partner.email)
        ):
            message += (
                "\n- Email address should be valid and not more then 100 charactor"
            )

        if not is_company:
            # TODO: check customer specific details
            pass

        if message:
            raise UserError(
                "Data not valid for the %s: %s\n%s"
                % (is_company and "Company" or "Customer", partner.name, message)
            )

    def button_l10n_in_submit_einvoice(self):
        self.ensure_one()

        if self.state != "posted":
            raise UserError(_("You can submit only confirmed invoice to GSTN Portal"))

        company = (
            self.journal_id.l10n_in_gstin_partner_id
            or self.journal_id.company_id.partner_id
        )
        customer = self.partner_id

        self._validate_invoice_data()
        self._validate_legal_identity_data(company, is_company=True)
        self._validate_legal_identity_data(customer)

        transaction = self.env["l10n.in.einvoice.transaction"]
        transaction_id = transaction.sudo().create({"move_id": self.id})
        self.l10n_in_transaction_id = transaction_id.id
        try:
            transaction_id.submit_invoice()
        except UserError as submit_invoice_error:
            _logger.info('Einvoice Json Response: %s', submit_invoice_error)
            if 'Duplicate IRN' in submit_invoice_error.name:
                try:
                    transaction_id.get_irn_by_details()
                except UserError as get_irn_error:
                    raise UserError("Duplicate IRN detected but %s \n Hint: Probably you want to cancel and re-create this invoice and submit it."%(get_irn_error.name))
            else:
                raise submit_invoice_error

    def button_l10n_in_cancel_einvoice(self):
        self.ensure_one()
        if self.state != "cancel":
            raise UserError(_("You cannot cancel IRN from %s state" % (self.state)))
        return self.env.ref(
            "l10n_in_einvoice_v16.l10n_in_einvoice_cancel_wizard_action"
        ).read()[0]

