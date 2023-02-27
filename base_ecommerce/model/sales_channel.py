from odoo import api, fields, models


class SalesChannel(models.Model):
    _name = "shop.sales.channel"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Sales Channel"

    seller_id = fields.Many2one("seller.merchant", "Seller/Merchant")
    name = fields.Char(string="Name", tracking=True)
    shop_instance_id = fields.Many2one(comodel_name="shop.instance", tracking=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id, tracking=True)
    # sales_channel_id = fields.Many2one(comodel_name="sales.channel", string="Sales Channel")
    stock_location_id = fields.Many2one("stock.location", string="Stock Location", tracking=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    sales_journal_id = fields.Many2one("account.journal", string="Sales Journal", tracking=True)
    brand_id = fields.Many2one("product.category", string="Brand", tracking=True)
    confirm_orders = fields.Boolean(string="Confirm Orders", tracking=True)
    confirm_delivery_orders = fields.Boolean(string="Confirm Delivery Orders", tracking=True)
    confirm_invoices = fields.Boolean(string="Confirm Invoices", tracking=True)
    is_consumable_product = fields.Boolean(string="Is Consumable Product", tracking=True)

    def name_get(self):
        return [(record.id, "%s - %s - %s" % (record.seller_id.name, record.location_code_id.location_code, record.name)) for record in self]
