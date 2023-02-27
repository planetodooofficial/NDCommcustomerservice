from lxml import etree
from odoo.tools.misc import formatLang, format_date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
import logging
_logger = logging.getLogger(__name__)

INV_LINES_PER_STUB = 9

# Inherited Account Fiscal Position Line Items
class AccountFiscalPositionTaxInherit(models.Model):
    _inherit = "account.fiscal.position.tax"

    account_id = fields.Many2one('account.account')

class FiscalPositionInherit(models.Model):
    _inherit = 'account.fiscal.position'

    state = fields.Selection([('inter', 'Inter'), ('intra', 'Intra')], string="state")
    gstin_unit = fields.Many2one('res.partner', string="GSTIN Unit")


class AccountDeducteeType(models.Model):
    _name = 'account.deductee.type'
    _description = 'Deductee Type'

    name = fields.Char(string='Type', required=True)

    _sql_constraints = [('type_uniq', 'unique(name)', 'Type should be Unique')]


class AccountTax(models.Model):
    _inherit = 'account.tax'

    section_name = fields.Char(string='Section Name')
    exempt_limit = fields.Integer(string='Exempt Limit')
    # payment_code = fields.Char(string='Payment Code')
    deductee_type_id = fields.Many2one('account.deductee.type', ondelete='restrict', copy=False)
    is_tds = fields.Boolean("Is TDS")
    is_a_default = fields.Boolean("Is a Default",default=False)
    gstin_unit_id = fields.Many2one('res.partner',"GSTIN Unit")

#
# class AccountAnalyticlInherit(models.Model):
#     _inherit = "account.analytic.line"
#
#     # for changing amt to negative if debit
#     @api.onchange('amount')
#     def change_to_negative(self):
#         if self.move_id.debit:
#             self.amount = -(self.amount)
#
class POAccountAccount(models.Model):
    _inherit = 'account.account'

    gstin_unit_id = fields.Many2one('res.partner', "GSTIN Unit")

class AccountHsnCode(models.Model):
    _name = 'hsn.code'
    _rec_name = 'hsnsac_code'
    _description = ' HSN / SAC Code'

    hsnsac_code = fields.Char(string='HSN/SAC Code')
    description = fields.Char('Description')
    type = fields.Selection([
        ('s', 'Sales'),
        ('p', 'Purchase'),
    ], 'Type')
    taxes_id = fields.Many2one('account.tax', copy=False)
    is_active = fields.Boolean("Is Active")

    @api.onchange('type')
    def tax_domain(self):
        if self.type == 's':
            tax_sales = self.env['account.tax'].search([('type_tax_use', '=', 'sale')])
            if tax_sales:
                return {'domain': {'taxes_id': [('id', 'in', tax_sales.ids)]}}

        if self.type == 'p':
            tax_purchase = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')])
            if tax_purchase:
                return {'domain': {'taxes_id': [('id', 'in', tax_purchase.ids)]}}


# class PrintCheckInherit(models.TransientModel):
#     _inherit = 'print.prenumbered.checks'
#
#     def print_report(self):
#         check_number = int(self.next_check_number)
#         number_len = len(self.next_check_number or "")
#         payments = self.env['account.payment'].browse(self.env.context['payment_ids'])
#         payments.filtered(lambda r: r.state == 'draft').action_post()
#         payments.filtered(lambda r: r.state == 'posted' and not r.is_move_sent).write({'is_move_sent': True})
#         acc_payment = self.env['account.payment'].search([])
#         for payment in payments:
#
#             payment.check_number = '%0{}d'.format(number_len) % check_number
#             check_number += 1
#         return payments.do_print_check_report()


















