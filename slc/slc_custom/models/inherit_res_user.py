from odoo import fields, api, models
from odoo.exceptions import UserError, ValidationError

class IneheritResUser(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        res = super(IneheritResUser, self).create(vals)
        res.action_id = self.env.ref('spreadsheet_dashboard.ir_actions_dashboard_action').id
        return res