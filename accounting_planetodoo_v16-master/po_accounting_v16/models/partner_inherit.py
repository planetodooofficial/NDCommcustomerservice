from odoo import models, fields, api, _


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    tds_tax_id = fields.Many2one('account.tax',string="Taxes")
    deductee_type_id = fields.Many2one('account.deductee.type', string='Deductive Type', copy=False)
