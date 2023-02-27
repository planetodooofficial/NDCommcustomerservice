from odoo import fields, models
from odoo.exceptions import *


class ShopImportLogs(models.Model):
    _name = "shop.import.logs"
    # _rec_name = 'id'
    start_date = fields.Datetime(string="Start DateTime")
    end_date = fields.Datetime(string="End DateTime")
    no_of_records = fields.Integer(string="No of Records")
    status = fields.Selection([('success', 'Success'),
                               ('exception', 'Exception'),
                               ], string="Status")

    log_exception = fields.Text(string="Log Exception")
    operation_performed = fields.Char(string="Operation Performed")
    shop_instance_id = fields.Many2one("shop.instance")
    company_id = fields.Many2one("res.company", string="Company")

    # Filters the order based on log import id
    def open_imported_order(self):
        order = self.env['sale.order'].search(['|', '|', ('log_id', '=', self.id), ('invoice_log_id', '=', self.id),
                                               ('order_update_log', '=', self.id)])
        domain = ['|', '|', ('log_id', '=', self.id), ('invoice_log_id', '=', self.id), ('order_update_log', '=', self.id)]
        if order:
            view_id = self.env.ref('sale.view_quotation_tree_with_onboarding').id
            context = self._context.copy()
            return {
                'name': self.shop_instance_id.instance_name + " Orders",
                'view_type': 'tree',
                'view_mode': 'tree',
                'views': [[self.env.ref('sale.view_quotation_tree_with_onboarding').id, 'list'],
                          [self.env.ref('sale.view_order_form').id, 'form']],
                'res_model': 'sale.order',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'domain': domain,
            }
        else:
            raise MissingError("Sorry No order Found For this Particular Log")
