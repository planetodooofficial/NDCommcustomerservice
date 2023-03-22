from odoo import api, fields, models
import pandas as pd
import base64
from io import BytesIO
from datetime import datetime


class ReasonWiz(models.TransientModel):
    _name = 'reasons.wiz'
    _description = 'Reason and Description Wizard'

    master_reason = fields.Many2one('reason.reasons', string="Select Reason")
    sale_id = fields.Many2one('sale.order')

    def log_message(self):
        sale_order = self.env['sale.order'].browse(self._context.get('active_id'))
        msg = f"Status -> Reject -> <ul><li>Reason: {self.master_reason.name}</li>"
        sale_order.message_post(body=msg)
        sale_order.update({'approval_status': "reject"})

