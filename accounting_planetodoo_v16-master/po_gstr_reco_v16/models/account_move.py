from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    reconciled = fields.Boolean(string='Reconciled')