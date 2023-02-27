from odoo import api, fields, models


class InheritResCountryState(models.Model):
    _inherit = "res.country.state"

    is_a_default = fields.Boolean("Is a Default", default=True)
