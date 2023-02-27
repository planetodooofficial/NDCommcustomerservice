from datetime import date
from odoo import fields, models


class AccountMoveInheritLine(models.Model):
    _inherit = 'account.move.line'

    overdue_days = fields.Integer(string='Overdue Days', compute='_get_overdue', store=True)
    hsn_code = fields.Char(string="HSN Code")

    def _get_overdue(self):
        for rec in self:
            if rec.date_maturity:
                todays_date = date.today()
                due_date = rec.date_maturity
                diff_days = todays_date - due_date
                rec.overdue_days = diff_days.days
            else:
                rec.overdue_days = 0
