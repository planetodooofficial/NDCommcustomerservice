from odoo import api, fields, models
import pandas as pd
import base64
from io import BytesIO
from datetime import datetime


class BulkCancellationWizard(models.TransientModel):
    _name = "bulk.cancellation.wizard"
    _description = "Bulk Cancellation Wizard"

    upload_file = fields.Binary("Upload File")
    company_id = fields.Many2one("res.company", "Company", readonly=True, default=lambda self: self.env.company.id)

    def action_bulk_cancel(self):
        filename = BytesIO(base64.b64decode(self.upload_file))
        data = pd.read_excel(filename)
        print(data.values)
        for order in data.values:
            print(order[0])
            sale_order_id = self.env['sale.order'].search([('name', '=', order[0])])
            if sale_order_id:
                sale_order_val = {
                    'cancellation': True,
                    'canc_req_datetime': datetime.today()
                }
                sale_order_id.write(sale_order_val)
