from odoo import api, fields, models


class SellerMerchant(models.Model):
    _name = "seller.merchant"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Seller/Merchant Name")
    exporter_name = fields.Char("Exporter Name")
    coa_id = fields.Many2one("account.account", "Ledger")