from odoo import api, fields, models


class InheritShopSalesChannel(models.Model):
    _inherit = "shop.sales.channel"

    location_code_id = fields.Many2one("locations.code", "Location Code")