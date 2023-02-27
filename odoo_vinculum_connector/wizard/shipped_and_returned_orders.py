import base64
from tempfile import TemporaryFile
import openpyxl
from odoo import api, fields, models


class ShippedReturnedOrderWizard(models.TransientModel):
    _name = "shipped.returned.order.wizard"
    _description = "Shipped Returned Order Wizard"

    shop_instance_id = fields.Many2one("shop.instance", string="Amazon Instance(s)")
    upload_file = fields.Binary("Upload File")
    company_id = fields.Many2one("res.company", "Company", readonly=True, default=lambda self: self.env.company.id)
    download_format = fields.Char("Download Format", readonly=True, default="https://ndcommercefileformate.csv")

    def action_import(self):
        pass