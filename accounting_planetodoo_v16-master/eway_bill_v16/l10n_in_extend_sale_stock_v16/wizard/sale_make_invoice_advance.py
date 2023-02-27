# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _default_has_different_wh_address(self):
        if self._context.get('active_model') == 'sale.order' and self._context.get('active_ids', False):
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids'))
            wh_address = sale_orders.mapped('order_line').filtered(
                lambda l: l.order_id.company_id.country_id.code == 'IN' and l.qty_to_invoice
                ).mapped('order_id.warehouse_id.partner_id')
            return len(wh_address) > 1
        return False

    has_different_wh_address = fields.Boolean(default=_default_has_different_wh_address, string='Has different WH address')