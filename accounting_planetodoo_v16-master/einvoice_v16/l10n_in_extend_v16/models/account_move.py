# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    tax_amount_by_lines = fields.Binary(
        string="Tax amount for lines",
        compute="_compute_invoice_taxes_by_line_by_group",
        help="Tax amount by group for the invoice line.",
    )

    tax_rate_by_lines = fields.Binary(
        string="Tax rate for lines",
        compute="_compute_invoice_taxes_rate_by_line_by_group",
        help="Tax rate by group for the invoice line.",
    )

    dispatch_partner_id = fields.Many2one(
        "res.partner",
        string="Dispatch Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Dispatch address for current invoice/bill.",
    )

    def _compute_invoice_taxes_rate_by_line_by_group(self):
        for invoice in self:
            taxes = dict()
            for line in invoice.invoice_line_ids:
                taxes[line.id] = line.tax_rate_by_tax_group
            invoice.tax_rate_by_lines = taxes

    def _compute_invoice_taxes_by_line_by_group(self):
        for invoice in self:
            taxes = dict()
            for line in invoice.invoice_line_ids:
                taxes[line.id] = line.tax_amount_by_tax_group
            invoice.tax_amount_by_lines = taxes

    @api.model
    def _get_tax_grouping_key_from_tax_line(self, tax_line):
        res = super()._get_tax_grouping_key_from_tax_line(tax_line)
        if self.country_code != "IN":
            return res

        res.update(
            {
                "base_line_ref": tax_line.ref,
            }
        )
        return res

    @api.model
    def _get_tax_grouping_key_from_base_line(self, base_line, tax_vals):
        res = super()._get_tax_grouping_key_from_base_line(base_line, tax_vals)
        if self.country_code != "IN":
            return res

        ref = base_line._origin.id or base_line.id.ref or base_line.id
        base_line.base_line_ref = ref
        res.update(
            {
                "base_line_ref": ref,
            }
        )
        return res

    @api.model
    def _get_tax_key_for_group_add_base(self, line):
        tax_key = super()._get_tax_key_for_group_add_base(line)
        if self.country_code != "IN":
            return tax_key
        tax_key += [
            line.id,
        ]
        return tax_key

    @api.model
    def _l10n_in_get_indian_state(self, partner):
        indian_state = super()._l10n_in_get_indian_state(partner)
        if partner.country_id and partner.country_id.code != "IN":
            return self.env.ref("l10n_in_extend_v16.state_in_oc")
        return indian_state

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        res.line_ids._update_base_line_ref()
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # it would be good to use the many2one fields instead of char, but required
    # framework fix for onchnage/create, we just need the referance to search the
    # related tax lines so char field would be ok as of now.
    base_line_ref = fields.Char(
        "Matching Ref",
        help="Technical field to map invoice base line with its tax lines.",
    )

    tax_amount_by_tax_group = fields.Binary(
        string="Tax amount by group",
        compute="_compute_invoice_line_taxes_by_group",
        help="Tax amount by group for the line.",
    )

    tax_rate_by_tax_group = fields.Binary(
        string="Tax rate by group",
        compute="_compute_invoice_line_taxes_by_group",
        help="Tax rate by group for the line.",
    )

    def _compute_invoice_line_taxes_by_group(self):
        # prepare the dict of tax values by tax group
        # line.tax_amount_by_tax_group = {'SGST': 9.0, 'CGST': 9.0, 'Cess': 2.0}
        # line.tax_rate_by_tax_group = {'SGST': 5, 'CGST': 5, 'Cess': 1}
        for line in self:
            move_id = line.move_id
            taxes = dict()
            taxes_rate = dict()
            for ln in self.search(
                [
                    ("base_line_ref", "=", str(line.id)),
                    ("tax_line_id", "!=", False),
                    ("move_id", "=", line.move_id.id),
                ]
            ):
                tax_group_name = ln.tax_line_id.tax_group_id.name.upper()
                if tax_group_name not in (
                    "SGST",
                    "CGST",
                    "IGST",
                    "CESS",
                    "UTGST",
                    "CESS-NON-ADVOL",
                    "STATE CESS",
                    "STATE CESS-NON-ADVOL",
                ):
                    tax_group_name = "OTHER"
                taxes.setdefault(tax_group_name, 0.0)
                if (
                    not self._context.get("in_company_currency")
                    and move_id.currency_id
                    and move_id.company_id.currency_id != move_id.currency_id
                ):
                    taxes[tax_group_name] += ln.amount_currency * (
                        move_id.is_inbound() and -1 or 1
                    )
                else:
                    taxes[tax_group_name] += ln.balance * (
                        move_id.is_inbound() and -1 or 1
                    )
                taxes_rate.setdefault(tax_group_name, 0.0)
                taxes_rate[tax_group_name] += ln.tax_line_id.amount
            line.tax_amount_by_tax_group = taxes
            line.tax_rate_by_tax_group = taxes_rate

    def _update_base_line_ref(self):
        # search for the invoice lines on which the taxes applied
        base_lines = self.filtered(lambda ln: ln.tax_ids)
        for line in base_lines:
            # filters the tax lines related to the base lines and replace virtual_id with the database id
            tax_lines = self.filtered(
                lambda ln: ln.tax_line_id
                and not ln.tax_ids
            )
            tax_lines += line
            tax_lines.write(
                {
                    "base_line_ref": line.id,
                }
            )

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #     lines._update_base_line_ref()
    #     return lines
