# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "l10n.in.ewaybill.mixin"]

    l10n_in_ewaybill_transaction_ids = fields.One2many(
        "l10n.in.ewaybill.transaction", "move_id", "Ewaybill transaction"
    )

    @api.depends("l10n_in_ewaybill_transaction_ids")
    def _compute_l10n_in_ewaybill_details(self):
        return super()._compute_l10n_in_ewaybill_details()

    def _get_ewaybill_transaction_domain(self):
        domain = super()._get_ewaybill_transaction_domain()
        domain += [("move_id", "=", self.id)]
        return domain

    def _generate_ewaybill_transaction(self, values):
        values.update({"move_id": self.id})
        return self.env["l10n.in.ewaybill.transaction"].create(values)

    def _compute_l10n_in_ewaybill_document_number(self):
        for move in self:
            move.l10n_in_ewaybill_document_number = (
                move.is_purchase_document(include_receipts=True)
                and move.ref
                or move.name
            )
            move.l10n_in_ewaybill_document_date = move.date

    def _compute_l10n_in_ewaybill_supply_type(self):
        super()._compute_l10n_in_ewaybill_supply_type()
        for move in self:
            if move.is_sale_document(include_receipts=True):
                move.l10n_in_ewaybill_supply_type = "O"
            if move.is_purchase_document(include_receipts=True):
                move.l10n_in_ewaybill_supply_type = "I"

    def _compute_l10n_in_ewaybill_bill_to(self):
        super()._compute_l10n_in_ewaybill_bill_to()
        for move in self:
            if move.l10n_in_ewaybill_supply_type == "O":
                move.l10n_in_ewaybill_bill_to = move.partner_id

    def _compute_l10n_in_ewaybill_ship_to(self):
        super()._compute_l10n_in_ewaybill_ship_to()
        for move in self:
            if move.l10n_in_ewaybill_supply_type == "O":
                move.l10n_in_ewaybill_ship_to = move.partner_id
                # move.l10n_in_ewaybill_ship_to = move.journal_id.l10n_in_gstin_partner_id

    def _compute_l10n_in_ewaybill_bill_from(self):
        super()._compute_l10n_in_ewaybill_bill_from()
        for move in self:
            if move.l10n_in_ewaybill_supply_type == "I":
                move.l10n_in_ewaybill_bill_from = move.partner_id

    def _compute_l10n_in_ewaybill_ship_from(self):
        super()._compute_l10n_in_ewaybill_ship_from()
        for move in self:
            if move.l10n_in_ewaybill_supply_type == "I":
                move.l10n_in_ewaybill_ship_from = move.partner_id

    def _prepare_validate_ewaybill_message(self):
        message = super()._prepare_validate_ewaybill_message()
        for move in self.invoice_line_ids:
            if not move.product_id.l10n_in_hsn_code:
                message += "\n- Product(%s) required HSN Code" % (move.product_id.name)
        return message

    def _compute_l10n_in_ewaybill_invoice_values_json(self):
        super()._compute_l10n_in_ewaybill_invoice_values_json()
        for move in self:
            move.l10n_in_ewaybill_invoice_values_json = {
                l.id: l.l10n_in_ewaybill_invoice_line_values_json
                for l in move.invoice_line_ids
            }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_in_ewaybill_invoice_line_values_json = fields.Binary(
        "Financial Data (JSON)",
        compute="_compute_l10n_in_ewaybill_invoice_line_values_json",
    )

    def _compute_l10n_in_ewaybill_invoice_line_values_json(self):
        invoices_lines = self.filtered(lambda l: l.tax_ids)
        (self - invoices_lines).l10n_in_ewaybill_invoice_line_values_json = {}
        for aml in invoices_lines:
            amount_sign = aml.move_id.is_inbound() and -1 or 1
            vals = {
                "amount_untaxed": sum(aml.mapped("balance")) * amount_sign,
                "amount_total": (
                    (aml.balance * amount_sign)
                    + sum(aml.tax_amount_by_tax_group.values())
                ),
                "price_unit": aml.balance / aml.quantity,
                "tax_amount_by_tax_group": aml.tax_amount_by_tax_group,
                "tax_rate_by_tax_group": aml.tax_rate_by_tax_group,
            }
            aml.l10n_in_ewaybill_invoice_line_values_json = vals
