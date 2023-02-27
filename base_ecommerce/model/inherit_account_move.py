from odoo import api, fields, models


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def sale_order_connection(self):
        date_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)]).date_order.strftime(
            "%b %d, %Y")
        return date_order

    def sale_order_pay(self):
        payment_method = self.env['sale.order'].search([('name', '=', self.invoice_origin)]).vinculum_payment_method
        return payment_method
