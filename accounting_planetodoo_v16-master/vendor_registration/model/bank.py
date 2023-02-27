from odoo import models, api, fields, _


class InheritBank(models.Model):
    _inherit = ['res.bank']

    swift_code = fields.Char('Swift Code')
    usd_account_name = fields.Char('USD Account Name')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
