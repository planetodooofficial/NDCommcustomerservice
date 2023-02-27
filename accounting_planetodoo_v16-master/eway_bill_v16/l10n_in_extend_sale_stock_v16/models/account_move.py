# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.company_id.country_id.code != 'IN' and not res.is_sale_document():
            return res
        dispatch_partner_id = res.mapped('invoice_line_ids.sale_line_ids.order_id.warehouse_id.partner_id')
        if not res.dispatch_partner_id and len(dispatch_partner_id) == 1:
            res.dispatch_partner_id = dispatch_partner_id
        return res
