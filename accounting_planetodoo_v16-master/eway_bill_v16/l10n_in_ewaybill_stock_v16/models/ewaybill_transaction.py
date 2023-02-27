# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class EwayBill(models.Model):
    _inherit = "l10n.in.ewaybill.transaction"

    picking_id = fields.Many2one("stock.picking", string="Stock Picking")

    def _get_source_document(self):
        source_document = super()._get_source_document()
        if self.picking_id:
            source_document += self.picking_id.name
        return source_document

    def _get_last_generate_request(self):
        if self.picking_id:
            last_generate_request = self.search(
                [
                    ("picking_id", "=", self.picking_id.id),
                    ("request_type", "=", "generate"),
                ],
                limit=1,
            )
            return last_generate_request
        return super()._get_last_generate_request()

    def _prepare_compute_request_json_template_values(self):
        values = super()._prepare_compute_request_json_template_values()
        if self.picking_id:
            values.update(
                {
                    "document": self.picking_id,
                    "document_line": self.picking_id.move_ids_without_package,
                    "is_picking": True,
                }
            )
        return values

    @api.depends("picking_id")
    def _compute_request_json(self):
        return super()._compute_request_json()

    def _get_company_partner(self):
        if self.picking_id:
            return self.picking_id.company_id.partner_id
        return super()._get_company_partner()
