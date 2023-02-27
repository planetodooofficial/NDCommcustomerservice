# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_l10n_in_ewaybill_ship_to(self):
        super()._compute_l10n_in_ewaybill_ship_to()
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                warehouse_partner_ids = record.line_ids.mapped(
                    "sale_line_ids.order_id.picking_ids.partner_id"
                )
                if warehouse_partner_ids:
                    record.l10n_in_ewaybill_ship_to = warehouse_partner_ids[0]

    def _compute_l10n_in_ewaybill_ship_from(self):
        super()._compute_l10n_in_ewaybill_ship_from()
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                picking_partner_ids = record.line_ids.mapped(
                    "sale_line_ids.order_id.picking_ids.picking_type_id.warehouse_id.partner_id"
                )
                if picking_partner_ids:
                    record.l10n_in_ewaybill_ship_from = picking_partner_ids[0]
