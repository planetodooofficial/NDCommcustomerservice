from odoo import api, fields, models


class SalesOrderInherit(models.Model):
    _inherit = "sale.order"

    shop_instance_id = fields.Many2one("shop.instance", string="Shop Instance", readonly=True)
    sales_channel_id = fields.Many2one("shop.sales.channel", string="Sales Channel", readonly=True)
    location_id = fields.Many2one("stock.location", "Location", readonly=True)
    is_exception = fields.Boolean("Is Exception")
    import_logs = fields.Text("Import Logs", readonly=True)
    l10n_in_journal_id = fields.Many2one('account.journal', string="Journal", compute="_compute_l10n_in_journal_id", store=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code', string="Country code")
    log_id = fields.Many2one('shop.import.logs')
    invoice_log_id = fields.Many2one('shop.import.logs')
    order_update_log = fields.Many2one('shop.import.logs')
    is_channel_exception = fields.Boolean("Is Channel exception")


class SalesOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    is_exception = fields.Boolean(string="Exception", default=False)
    stock_loc_id = fields.Many2one('stock.location')