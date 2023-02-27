# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _compute_l10n_in_ewaybill_bill_to(self):
        super()._compute_l10n_in_ewaybill_bill_to()
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                partner_ids = record.mapped(
                    "move_ids.sale_line_id.order_id.invoice_ids.partner_id"
                )
                if partner_ids:
                    record.l10n_in_ewaybill_bill_to = partner_ids[0]

    def _compute_l10n_in_ewaybill_bill_from(self):
        super()._compute_l10n_in_ewaybill_bill_from()
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                gstin_partner_ids = record.mapped("move_ids.sale_line_id.order_id.invoice_ids.journal_id.l10n_in_gstin_partner_id")
                if gstin_partner_ids:
                    record.l10n_in_ewaybill_bill_from = gstin_partner_ids[0]
