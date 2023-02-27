from odoo import api, fields, models


class LocationsCode(models.Model):
    _name = "locations.code"
    _rec_name = "location_code"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    location_code = fields.Char("Location Code")