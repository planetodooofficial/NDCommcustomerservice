from odoo import api, fields, models


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    mrp = fields.Float(string="MRP")
    is_exception = fields.Boolean(string="Exception", default=False)