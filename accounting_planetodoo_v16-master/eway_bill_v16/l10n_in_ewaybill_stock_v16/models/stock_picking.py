# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "l10n.in.ewaybill.mixin"]

    l10n_in_ewaybill_transaction_ids = fields.One2many(
        "l10n.in.ewaybill.transaction", "picking_id", "Ewaybill transaction"
    )

    @api.depends("l10n_in_ewaybill_transaction_ids")
    def _compute_l10n_in_ewaybill_details(self):
        return super()._compute_l10n_in_ewaybill_details()

    def _get_ewaybill_transaction_domain(self):
        domain = super()._get_ewaybill_transaction_domain()
        domain += [("picking_id", "=", self.id)]
        return domain

    def _generate_ewaybill_transaction(self, values):
        values.update({"picking_id": self.id})
        return self.env["l10n.in.ewaybill.transaction"].create(values)

    def _compute_l10n_in_ewaybill_document_number(self):
        for picking in self:
            picking.l10n_in_ewaybill_document_number = picking.name
            picking.l10n_in_ewaybill_document_date = picking.date_done

    def _compute_l10n_in_ewaybill_supply_type(self):
        super()._compute_l10n_in_ewaybill_supply_type()
        supply_type_code = {"incoming": "I", "outgoing": "O"}
        for picking in self:
            picking.l10n_in_ewaybill_supply_type = supply_type_code.get(
                picking.picking_type_id.code, ""
            )

    def _compute_l10n_in_ewaybill_bill_to(self):
        super()._compute_l10n_in_ewaybill_bill_to()
        for picking in self:
            if picking.l10n_in_ewaybill_supply_type == "O":
                picking.l10n_in_ewaybill_bill_to = picking.partner_id

    def _compute_l10n_in_ewaybill_ship_to(self):
        super()._compute_l10n_in_ewaybill_ship_to()
        for picking in self:
            if picking.l10n_in_ewaybill_supply_type == "O":
                picking.l10n_in_ewaybill_ship_to = picking.partner_id
            if (
                picking.l10n_in_ewaybill_supply_type == "I"
                and picking.picking_type_id.warehouse_id.partner_id
            ):
                picking.l10n_in_ewaybill_ship_to = (
                    picking.picking_type_id.warehouse_id.partner_id
                )

    def _compute_l10n_in_ewaybill_bill_from(self):
        super()._compute_l10n_in_ewaybill_bill_from()
        for picking in self:
            if picking.l10n_in_ewaybill_supply_type == "I":
                picking.l10n_in_ewaybill_bill_from = picking.partner_id

    def _compute_l10n_in_ewaybill_ship_from(self):
        super()._compute_l10n_in_ewaybill_ship_from()
        for picking in self:
            if (
                picking.l10n_in_ewaybill_supply_type == "O"
                and picking.picking_type_id.warehouse_id.partner_id
            ):
                picking.l10n_in_ewaybill_ship_from = (
                    picking.picking_type_id.warehouse_id.partner_id
                )
            if picking.l10n_in_ewaybill_supply_type == "I":
                picking.l10n_in_ewaybill_ship_from = picking.partner_id

    def _prepare_validate_ewaybill_message(self):
        message = super()._prepare_validate_ewaybill_message()
        for move in self.move_ids_without_package:
            if not move.product_id.l10n_in_hsn_code:
                message += "\n- Product(%s) required HSN Code" % (move.product_id.name)
        return message

    def _compute_l10n_in_ewaybill_invoice_values_json(self):
        super()._compute_l10n_in_ewaybill_invoice_values_json()
        for picking in self:
            picking.l10n_in_ewaybill_invoice_values_json = {
                line.id: line.l10n_in_ewaybill_invoice_line_values_json
                for line in picking.move_ids_without_package
            }
