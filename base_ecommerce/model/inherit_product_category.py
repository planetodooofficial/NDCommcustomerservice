from odoo import api, fields, models


class ProductCategoryInherit(models.Model):
    _inherit = "product.category"

    code = fields.Char("Code")