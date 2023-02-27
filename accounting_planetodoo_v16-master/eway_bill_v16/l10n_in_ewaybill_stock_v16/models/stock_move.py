# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    l10n_in_ewaybill_invoice_line_values_json = fields.Binary(
        "Financial Data (JSON)",
        compute="_compute_l10n_in_ewaybill_invoice_line_values_json",
    )

    def _compute_l10n_in_ewaybill_invoice_line_values_json(self):
        FiscalPosition = self.env["account.fiscal.position"]
        for line in self:
            tax_amount_by_tax_group = {}
            tax_rate_by_tax_group = {}
            product = line.product_id
            price_unit = product.lst_price
            partner = line.picking_id.partner_id
            fiscal_position_id = FiscalPosition._get_fiscal_position(partner,None)
            # Check: sale and purchase can be different!!
            if line.picking_id.l10n_in_ewaybill_supply_type == "O":
                tax_ids = product.taxes_id.filtered(
                    lambda t: t.company_id == line.company_id
                )
            else:
                tax_ids = product.supplier_taxes_id.filtered(
                    lambda t: t.company_id == line.company_id
                )
            taxes_id = fiscal_position_id.map_tax(tax_ids)
            taxes = taxes_id.compute_all(
                price_unit,
                quantity=line.quantity_done,
                product=product,
                partner=partner,
            )
            for tax in taxes.get("taxes"):
                tax_id = self.env["account.tax"].browse(tax.get("id"))
                # tax amount by group
                tax_group_name = tax_id.tax_group_id.name.upper()
                if tax_group_name not in (
                    "SGST",
                    "CGST",
                    "IGST",
                    "CESS",
                    "CESS-NON-ADVOL",
                    "STATE CESS",
                    "STATE CESS-NON-ADVOL",
                ):
                    tax_group_name = "OTHER"
                # in eway-bill there is no separate value for state cess so merge that in normal cess
                tax_group_name = (
                    (tax_group_name == "STATE CESS-NON-ADVOL")
                    and "CESS-NON-ADVOL"
                    or tax_group_name
                )
                tax_group_name = (
                    (tax_group_name == "STATE CESS") and "CESS" or tax_group_name
                )
                tax_amount_by_tax_group.setdefault(tax_group_name, 0.0)
                tax_amount_by_tax_group[tax_group_name] += tax.get("amount")
                # tax rate by group
                tax_rate_by_tax_group.setdefault(tax_group_name, 0.0)
                tax_rate_by_tax_group[tax_group_name] += tax_id.amount

            line.l10n_in_ewaybill_invoice_line_values_json = {
                "amount_untaxed": taxes.get("total_excluded"),
                "amount_total": taxes.get("total_included"),
                "price_unit": taxes.get("total_excluded") / line.quantity_done,
                "tax_amount_by_tax_group": tax_amount_by_tax_group,
                "tax_rate_by_tax_group": tax_rate_by_tax_group,
            }
