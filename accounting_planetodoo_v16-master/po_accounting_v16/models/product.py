from odoo.tools.misc import formatLang, format_date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
import logging

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    purchase_hsn = fields.Many2one('hsn.code',string='Purchase HSN', domain="[('type', '=', 'p')]")
    sale_hsn = fields.Many2one('hsn.code',string='Sales HSN', domain="[('type', '=', 's')]")
    sales_hsn_description = fields.Char(string='Sales HSN Description')
    purchase_hsn_description = fields.Char(string='Purchase HSN Description')

    @api.onchange('purchase_hsn')
    def purchase_hsn_code(self):
        if self.purchase_hsn:
            # self.l10n_in_hsn_code = self.purchase_hsn
            self.purchase_hsn_description = self.purchase_hsn.description

    @api.onchange('sale_hsn')
    def sale_hsn_code(self):
        if self.sale_hsn.hsnsac_code:
            self.l10n_in_hsn_code = self.sale_hsn.hsnsac_code
            self.sales_hsn_description = self.sale_hsn.description

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    purchase_hsn = fields.Many2one('hsn.code',string='Purchase HSN', domain="[('type', '=', 'p')]")
    sale_hsn = fields.Many2one('hsn.code',string='Sales HSN', domain="[('type', '=', 's')]")
    sales_hsn_description = fields.Char(string='Sales HSN Description')
    purchase_hsn_description = fields.Char(string='Purchase HSN Description')

    @api.onchange('purchase_hsn')
    def purchase_hsn_code(self):
        if self.purchase_hsn:
            # self.l10n_in_hsn_code = self.purchase_hsn
            self.purchase_hsn_description = self.purchase_hsn.description

    @api.onchange('sale_hsn')
    def purchase_hsn_code(self):
        if self.sale_hsn.hsnsac_code:
            self.l10n_in_hsn_code = self.sale_hsn.hsnsac_code
            self.sales_hsn_description = self.sale_hsn.description