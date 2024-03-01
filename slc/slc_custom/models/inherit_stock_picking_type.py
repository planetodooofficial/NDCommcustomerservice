from odoo import fields, api, models


class InheritStockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    finished_goods = fields.Boolean(string='Finished Goods', default=False)
    vehicle_otl_details = fields.Boolean(string='Vehicle/OTL details applicable', default=False)
    delivery_challan_details = fields.Boolean(string='Delivery Challan Details applicable', default=False)
    sale_invoice_details = fields.Boolean(string='Sale Invoice Details applicable', default=False)
    export_details = fields.Boolean(string='Export Details applicable', default=False)
