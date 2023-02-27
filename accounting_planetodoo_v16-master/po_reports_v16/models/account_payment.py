from odoo import  api, fields, models, _
from odoo.exceptions import UserError
# import xmltodict


class AccountPayment(models.Model):
    _inherit = "account.payment"

    account_payment_line_ids = fields.One2many('account.payment.line', 'payment_id', string='Journal Items', copy=True)
    # process_move_lines(self, data):

    def action_post(self):
        res = super().action_post()
        if self.account_payment_line_ids:
            total_paid = sum(self.account_payment_line_ids.mapped('amt_paid'))
            if total_paid != self.amount:
                raise UserError("Total invoice Amount paid and payment amount should be same!")

            mv_line_ids =[]
            if self.payment_type == 'inbound':
                move_line_id = self.move_id.line_ids.filtered(lambda v: v.account_id.id == self.partner_id.property_account_receivable_id.id)
                mv_line_ids.append(move_line_id.id)
                for inv in self.account_payment_line_ids:
                    inv_move_line_id = inv.invoice_id.line_ids.filtered(
                        lambda v: v.account_id.id == self.partner_id.property_account_receivable_id.id)
                    mv_line_ids.append(inv_move_line_id.id)
            else:
                move_line_id = self.move_id.line_ids.filtered(
                    lambda v: v.account_id.id == self.partner_id.property_account_payable_id.id)
                mv_line_ids.append(move_line_id.id)
                for inv in self.account_payment_line_ids:
                    inv_move_line_id = inv.invoice_id.line_ids.filtered(
                        lambda v: v.account_id.id == self.partner_id.property_account_payable_id.id)
                    mv_line_ids.append(inv_move_line_id.id)

            # 'new_mv_line_dicts': [
            #     {
            #         'credit': 18.04,
            #         'debit': 0.00,
            #         'journal_id': self.bank_journal_euro.id,
            #         'name': 'Total WriteOff (Fees)',
            #         'account_id': self.diff_expense_account.id
            #     }
            # ]

            data_for_reconciliation =[{'id': None, 'type': None, 'mv_line_ids': mv_line_ids, 'new_mv_line_dicts': []}]

            if mv_line_ids:
                self.env["account.reconciliation.widget"].process_move_lines(data_for_reconciliation)
                # mv_line = self.env["account.move.line"].browse(mv_line_ids)
                # mv_line.reconcile()

                # for line in mv_line:
                #     line.reconciled
        return res


class AccountPaymentLine(models.Model):
    _name = "account.payment.line"

    payment_id = fields.Many2one('account.payment', string='Payment', required=True )
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True,)
    partner_id = fields.Many2one('res.partner',related='invoice_id.partner_id', string='Partner', required=True)
    amt = fields.Float(string='Amount')
    amt_paid = fields.Float(string='Pay Amount')
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', related='payment_id.payment_type')
    currency_id = fields.Many2one('res.currency',related='invoice_id.currency_id',readonly=True,string='Currency',)

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        self.amt_paid = self.invoice_id.amount_residual
        self.amt = self.invoice_id.amount_residual

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type == 'inbound':
            return {'domain': {'invoice_id': [('move_type', 'in', ('out_invoice', 'in_refund')),
                                              ('partner_id', '=', self.payment_id.partner_id.id),
                                              ('amount_residual', '!=', 0.0)]}}
        else:
            return {'domain': {'invoice_id': [('move_type', 'in', ('in_invoice', 'out_refund')),
                                              ('partner_id', '=', self.payment_id.partner_id.id),
                                              ('amount_residual', '!=', 0.0)]}}
